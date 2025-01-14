import cv2
import pymupdf
import numpy as np
from PIL import Image
from PIL import ImageFilter
import numpy as np
import pytesseract

from django.conf import settings


def tesseract(img):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
    print(text)


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
        tesseract(antied)
        processed_images.append(antied)
    return processed_images
