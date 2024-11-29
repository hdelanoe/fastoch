import logging
import cv2
import re
import pyzbar.pyzbar as pyzbar
from pyzbar.wrapper import ZBarSymbol

logger = logging.getLogger('fastoch')

class bar_decoder():

    def decode(filepath):
        img = cv2.imread(filepath)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        barcodes = pyzbar.decode(gray, [ZBarSymbol.EAN13, ZBarSymbol.EAN5])
        logger.debug(barcodes)
        if not barcodes:
            return None
        barcode = re.search(r'([0-9]+)', str(barcodes[0].data)).group(1)
        logger.debug(f'barcode = {barcode}')
        return barcode
