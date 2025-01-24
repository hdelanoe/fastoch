import PIL
import cv2
import pymupdf
import numpy as np
import pandas as pd
from PIL import Image
from PIL import ImageFilter
import numpy as np
import pytesseract
from heic2png import HEIC2PNG


from django.conf import settings


def tesseract(img):
    if settings.DEBUG:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
    find = [m.start() for m in re.finditer('\s([0-9]{13})\s', text)]
    eans = []
    for f in find:
        ean = text[f+1:f+14]
        eans.append(ean)
    return text


def apply_antialiasing(image, blur_strength=10):
    # Convertir l'image PIL en tableau NumPy
    if isinstance(image, Image.Image):
        image = np.array(image)

    # Vérifier si l'image est en niveaux de gris (2D)
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Appliquer le flou gaussien
    blurred = cv2.GaussianBlur(
        image,
        (0, 0),  # Laisser OpenCV déterminer la taille du noyau
        sigmaX=blur_strength,
        sigmaY=blur_strength
    )

    # Binarisation pour augmenter le contraste
    _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)

    # Retourner une image PIL
    return Image.fromarray(binary)

def lanczos(img):
    return img.resize((img.width // 2, img.height // 2), resample=Image.LANCZOS)

def resize(image_path):
    image = cv2.imread(image_path)
    scale_percent = 200 # percent of original size
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)

    # resize image
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    cv2.imwrite(image_path, resized )

def thresh(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # threshold the image using Otsu's thresholding method
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    dist = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)
    # normalize the distance transform such that the distances lie in
    # the range [0, 1] and then convert the distance transform back to
    # an unsigned 8-bit integer in the range [0, 255]
    dist = cv2.normalize(dist, dist, 0, 1.0, cv2.NORM_MINMAX)
    dist = (dist * 255).astype("uint8")
    cv2.imshow("Dist", dist)
    # threshold the distance transform using Otsu's method
    dist = cv2.threshold(dist, 0, 255,
        cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    cv2.imwrite(image_path, thresh)

def dist(image_path):
    # Charger l'image
    image = cv2.imread(image_path)

    # Vérifier si l'image a été correctement chargée
    if image is None:
        raise ValueError(f"Impossible de lire l'image à l'emplacement : {image_path}")

    # Convertir l'image en niveaux de gris
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Binariser l'image (méthode d'Otsu)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Appliquer la transformation de distance
    dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

    # Normaliser la transformation de distance pour qu'elle soit dans la plage [0, 1]
    dist = cv2.normalize(dist, dist, 0, 1.0, cv2.NORM_MINMAX)

    # Convertir la transformation normalisée en uint8 (plage [0, 255])
    dist = (dist * 255).astype("uint8")

    # Binariser la transformation de distance (seuil avec Otsu)
    dist = cv2.threshold(dist, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Sauvegarder l'image résultante
    cv2.imwrite(image_path, dist)

def binarize_image(pix):
    np_image = np.array(pix)  # Convertir Pixmap en tableau NumPy
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(binary)

def enhance_edges(image):
    return image.filter(ImageFilter.EDGE_ENHANCE)

def inverte(image_path):
    # Lire l'image
    image = cv2.imread(image_path)

    # Vérifiez si l'image a été chargée correctement
    if image is None:
        raise ValueError(f"Impossible de lire l'image à l'emplacement : {image_path}")

    # Inverser les couleurs
    image = cv2.bitwise_not(image)

    # Sauvegarder l'image inversée
    cv2.imwrite(image_path, image)

def process_png(filepath):
    processed_images = []
    doc = pymupdf.open(filepath)  # ouvrir le document
    for page in doc:
        dpi = 1200  # choisir le dpi désiré
        zoom = dpi / 106  # facteur de zoom
        magnify = pymupdf.Matrix(zoom, zoom)  # zoomer en x et y
        pix = page.get_pixmap(matrix=magnify)  # rendre la page en image

        # Convertir Pixmap en image PIL
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        #resize = lanczos(image)

        processed_images.append(image)
    return processed_images

def convert_heic_to_png(filename, file_path):
    # Conversion HEIC -> PNG
    try:
        heic_image = HEIC2PNG(file_path, quality=90)
        png_path = heic_image.save(f'{filename}.png')
        return png_path
    except:
        return None

def image_processing(image_path):

    #inverte(image_path)
    #logger.debug('inverted')

    #resize(image_path)
    #logger.debug('resized')

    thresh(image_path)
    logger.debug('threshed')

    #dist(image_path)
    #logger.debug('disted')

def xlsx_to_csv(xlsx_path):
    read_file = pd.read_excel (xlsx_path)

    # Write the dataframe object
    # into csv file
    read_file.to_csv (f'{settings.MEDIA_ROOT}/Test.csv',
                  index = None,
                  header=True)

    # read csv file and convert
    # into a dataframe object
    return f'{settings.MEDIA_ROOT}/Test.csv'
