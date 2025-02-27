# Set the python version as a build-time argument
# with Python 3.12 as the default
ARG PYTHON_VERSION=3.10-slim-bullseye
FROM python:${PYTHON_VERSION}

# Create a virtual environment
RUN python -m venv /opt/venv

# Set the virtual environment as the current location
ENV PATH=/opt/venv/bin:$PATH

# Upgrade pip
RUN python -m pip install --upgrade pip

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


    # Install os dependencies for our mini vm
RUN apt-get update && apt-get install -y \
    gcc \
    # for postgres
    libpq-dev \
    # for Pillow
    libjpeg-dev \
    # for CairoSVG
    libcairo2 \
    # for nvm
    curl \
    # for paddle
    python3-matplotlib \
    # other
    poppler-utils \
    libzbar0 \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*


# Create the mini vm's code directory
RUN mkdir -p /code/staticfiles/theme/
RUN mkdir -p /code/staticfiles/tw/
RUN chmod -R 755 /code/staticfiles
RUN chmod -R 755 /code/local-cdn


# Create log directory
RUN mkdir -p /code/logs
ENV LOGFILE_PATH=/code/logs/debug.log

# Set the working directory to that same code directory
WORKDIR /code

# Copy the requirements file into the container
COPY requirements.txt /tmp/requirements.txt

# copy the project code into the container's working directory
COPY ./src /code

# Install the Python project requirements
RUN python -m pip install --upgrade setuptools
RUN pip install -r /tmp/requirements.txt

# installe nvm (Gestionnaire de version node)
#ENV NODE_VERSION=22.11.0
#RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
#ENV NVM_DIR=/root/.nvm
#RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
#RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
#RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
#ENV PATH="$NVM_DIR/versions/node/v${NODE_VERSION}/bin/:${PATH}"


ARG DJANGO_SECRET_KEY
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
ENV DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME}
ENV DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}
ENV DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}
ENV MISTRAL_API_KEY=${MISTRAL_API_KEY}

ARG DJANGO_DEBUG=0
ENV DJANGO_DEBUG=${DJANGO_DEBUG}


# build css theme
#COPY ./package.json /code
#COPY ./tailwind.config.js /code
#RUN npm install -D tailwindcss
#RUN npm run build

# database isn't available during build
# run any other commands that do not need the database
# such as:
RUN python manage.py vendor_pull
RUN python manage.py collectstatic --noinput

# whitenoise -> s3

# set the Django default project name
ARG PROJ_NAME="home"

# create a bash script to run the Django project
# this script will execute at runtime when
# the container starts and the database is available
RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./paracord_runner.sh && \
    printf "python manage.py makemigrations --no-input\n" >> ./paracord_runner.sh && \
    printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
    printf "python manage.py createsuperuser --no-input --username \$DJANGO_SUPERUSER_USERNAME --email \$DJANGO_SUPERUSER_EMAIL\n" >> ./paracord_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --timeout 0 --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./paracord_runner.sh


# make the bash script executable
RUN chmod +x paracord_runner.sh

# Clean up apt cache to reduce image size
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run the Django project via the runtime script
# when the container starts
CMD ./paracord_runner.sh
