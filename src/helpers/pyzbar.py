import os
import logging
import cv2
import re
import pyzbar.pyzbar as pyzbar
from pyzbar.wrapper import ZBarSymbol

logger = logging.getLogger('fastoch')

class bar_decoder():

    @staticmethod
    def decode(filepath):
        try:
            # Vérifiez que le chemin est une chaîne ou un Path-like object
            if not isinstance(filepath, (str, os.PathLike)):
                filepath = str(filepath)

            # Vérifiez que le fichier existe
            if not os.path.exists(filepath):
                logger.error(f"File does not exist: {filepath}")
                return None

            # Chargez l'image
            img = cv2.imread(filepath)
            if img is None:
                logger.error(f"cv2.imread failed to load image: {filepath}")
                return None

            # Conversion en niveaux de gris
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Détection des codes-barres
            barcodes = pyzbar.decode(gray, [ZBarSymbol.EAN13, ZBarSymbol.EAN5])
            logger.debug(barcodes)

            if not barcodes:
                return None

            # Extraction du code-barres
            barcode = re.search(r'([0-9]+)', str(barcodes[0].data)).group(1)
            logger.debug(f'barcode = {barcode}')
            return barcode

        except Exception as e:
            logger.error(f'Error during barcode decoding: {e}')
            return None