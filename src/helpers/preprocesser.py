import cv2
import re
import pymupdf
import numpy as np
from PIL import Image
from PIL import ImageFilter
import numpy as np
import pytesseract
import logging
from heic2png import HEIC2PNG


from django.conf import settings

logger = logging.getLogger('fastoch')

def tesseract(img):
    if settings.DEBUG:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
    find = [m.start() for m in re.finditer('\s([0-9]{13})\s', text)]
    eans = []
    for f in find:
        ean = text[f+1:f+14]
        eans.append(ean)
    logger.debug(eans)    
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

def binarize_image(pix):
    np_image = np.array(pix)  # Convertir Pixmap en tableau NumPy
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(binary)

def enhance_edges(image):
    return image.filter(ImageFilter.EDGE_ENHANCE)

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
        
        # Binariser l'image
        #binarized_image = binarize_image(image)
        
        # Appliquer l'anti-aliasing
        #anti_aliased = apply_antialiasing(binarized_image)
        antied = lanczos(image)

        # remove tesseract for now
        text = tesseract(antied)

        processed_images.append(antied)
        process_return = {'text': text, 'processed_images': processed_images }
    return process_return

def convert_heic_to_png(filename, file_path):
    # Conversion HEIC -> PNG
    try:
        heic_image = HEIC2PNG(file_path, quality=90)
        png_path = heic_image.save(f'{filename}.png')
        return png_path
    except:
        return None
