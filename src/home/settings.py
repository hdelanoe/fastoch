import os
from pathlib import Path
from decouple import config
from concurrent_log_handler import ConcurrentRotatingFileHandler


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Email config
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', cast=str, default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', cast=str, default='587') # Recommanded
EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=str, default=None)
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str, default=None)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True) # Use EMAIL_PORT 587 for TLS
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool, default=False) # Use EMAIL_PORT 465 for SSL


MEDIA_DIRECTORY_PATH = config('MEDIA_DIRECTORY_PATH', cast=str, default=str(BASE_DIR / '../media/'))
#TESSERACT_PATH = config('TESSERACT_PATH', cast=str, default=False)


ADMINS=[('Fort Loop', 'contact@fortloop.fr')]
MANAGERS=ADMINS

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DJANGO_DEBUG', cast=bool, default=False)

BASE_URL = config('BASE_URL', default=None)

ALLOWED_HOSTS = [
    '.railway.app'
]

if DEBUG:
    ALLOWED_HOSTS += [
        '127.0.0.1',
        'localhost',
    ]


# Application definition

INSTALLED_APPS = [
    # django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third-party apps
    'allauth_ui',
    'allauth',
    'allauth.account',
    "widget_tweaks",
    "slippers",
    # my apps
    'commando',
    'dashboard',
    'settings',
    'inventory',
    'backup',
    'provider',
    'delivery',
]

MIDDLEWARE = [
    # Django
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # third parties
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "allauth.account.middleware.AccountMiddleware",

]

ROOT_URLCONF = 'home.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'home.wsgi.application'

# Chemin du fichier de log
LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)  # Crée le répertoire logs s'il n'existe pas
LOG_FILE_PATH = LOG_DIR / "fastoch.log"

LOGGING = {
    "version": 1,  # Version de la configuration de logging
    "disable_existing_loggers": False,  # Ne pas désactiver les loggers par défaut de Django
    "formatters": {
        "verbose": {  # Format détaillé pour les messages de log
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",  # Utilise les accolades `{}` pour le style
        },
        "simple": {  # Format simplifié (pour la console par exemple)
            "format": "{levelname}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {  # Handler pour afficher les logs dans la console
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",  # Utilise le format simple
        },
         "file": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOG_FILE_PATH,
            "when": "midnight",       # Rotation quotidienne
            "interval": 1,            # Tous les jours
            "backupCount": 7,         # Conserver 7 fichiers
            "formatter": "verbose",
        },
    },
    "loggers": {
        "fastoch": {  # Logger pour l'application Fastoch
            "handlers": ["console", "file"],  # Envoie les logs à la console et dans le fichier
            "level": "DEBUG",  # Niveau minimal pour ce logger
            "propagate": True,  # Propagation des logs aux autres loggers parents
        },

    },
    # Optionnel : loggers pour les bases de données
    # 'loggers': {
    #     'django.db.backends': {  # Logs pour les requêtes SQL exécutées
    #         'level': 'DEBUG',
    #         'handlers': ['console'],
    #         'propagate': False,
    #     },
    # },
}


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CONN_MAX_AGE = config("CONN_MAX_AGE", cast=int, default=300)
DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL is not None:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=CONN_MAX_AGE,
            conn_health_checks=True,
            ssl_require=True,  # Force l'utilisation de SSL
        )
    }
     # Ajoute manuellement les options SSL pour s'assurer qu'elles sont bien transmises
    DATABASES['default']['OPTIONS'] = DATABASES['default'].get('OPTIONS', {})
    DATABASES['default']['OPTIONS'].update({
        'sslmode': 'require',
    })



# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Django Allauth Config
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED=True
LOGIN_REDIRECT_URL='/'

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATICFILES_BASE_DIR = BASE_DIR / "staticfiles"
STATICFILES_BASE_DIR.mkdir(exist_ok=True, parents=True)
STATICFILES_VENDOR_DIR = STATICFILES_BASE_DIR / "vendors"

# source(s) for python manage.py collectstatic
STATICFILES_DIRS = [
    STATICFILES_BASE_DIR
]

# output for python manage.py collectstatic
# local cdn
STATIC_ROOT = BASE_DIR / "local-cdn"


#if not DEBUG:
#    STATIC_ROOT = BASE_DIR / 'prod-cdn'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.parent / 'media'


STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://tarrabio-staging.up.railway.app',
    'https://tarrabio-prod.up.railway.app',
    'https://fastoch-test.up.railway.app',
    ]

KESIA2_COLUMNS_NAME = {
    "code_art": "IDART",
    "provider": "NOM_FOURNISSEUR",
    "ean": "EAN",
    "multicode": "CODE",
    "description": "DEF",
    "quantity": "STOCK",
    "achat_ht": "PMPA",
}

INVENTORY_COLUMNS_NAME = {
    "multicode": "CODE",
    "provider": "NOM_FOURNISSEUR",
    "ean": "EAN",
    "description": "DEF",
    "quantity": "STOCK",
    "achat_ht": "PMPA",
}

DELIVERY_COLUMNS_NAME = {
    "multicode": "CODE",
    "ean": "EAN",
    "description": "DEF",
    "quantity": "STOCK",
    "achat_ht": "PMPA",
}