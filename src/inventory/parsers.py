import os
import logging
import re
import json
import pandas as pd

from django.core.files.storage import FileSystemStorage
from django.contrib import messages

from django.conf import settings
from inventory.models import Product, Transaction
from provider.models import Provider
from delivery.models import Delivery


from helpers.mistral import Mistral_API, Codestral_Mamba, format_content_from_image_path
from pdf2image import convert_from_path

logger = logging.getLogger('fastoch')

def file_to_json(request, uploaded_file, file_extension):
    fs = FileSystemStorage()
    filename = fs.save(uploaded_file.name, uploaded_file)
    file_path = fs.path(filename)
    if file_extension == ".pdf":
        pages = convert_from_path(file_path, 2000, jpegopt='quality', use_pdftocairo=True, size=(None,1080))
        api = Mistral_API()
        image_content = []
        try:
            for count, page in enumerate(pages):
                page.save(f'{settings.MEDIA_ROOT}/pdf{count}.jpg', 'JPEG')
                jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                image_content.append(format_content_from_image_path(jpg_path))
            try:
                json_data = api.extract_json_from_image(image_content)
            except Exception as e:
                logger.error(f"Error while extracting data from pdf with mistral - {e}")
                messages.error(request, "Erreur lors de la lecture du .pdf")
            for count, page in enumerate(pages):
                jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                fs.delete(jpg_path)
        except Exception as e:
            logger.error(f"Error while saving file - {e}")
            messages.error(request, "Erreur lors de la lecture du .pdf")
    else:
        try:
            if file_extension == ".xlsx" or file_extension == ".xls":
                df = pd.read_excel(file_path)
            elif file_extension == ".xml":
                df = pd.read_xml(file_path, encoding='utf-8')
            elif file_extension == ".csv":
                df = pd.read_csv(file_path, encoding='utf-8')
        except Exception as e:
            logger.error(f"Error while reading {file_extension} - {e}")
            messages.error(request, f"Erreur lors de la lecture du {file_extension}")        
        try:
            json_data = json.loads(df.to_json(orient='records'))
        except Exception as e:
            logger.error(f"Error while loading df in json - {e}")
            messages.error(request, f"Erreur lors de la lecture du {file_extension}")
    fs.delete(file_path)
    return (json_data)

def json_to_db(providername, json_data, inventory, operator=1):
    logger.debug("json_to_db")
    # format return obj
    delivery = Delivery.objects.create(inventory=inventory)
    return_obj = {'delivery': delivery, 'error_list': []}
    item_count = 0

    # get or create provider
    provider, created = Provider.objects.get_or_create(
        name=providername,
        code=str(providername).replace(' ', '')[:3].upper())
    if created:
        provider.save()

    for jd in json_data:
        try:
            logger.debug(
                        f'{kesia_get(jd, 'provider')}'
                        f'{kesia_get(jd, 'code_art')}'
                        f'{kesia_get(jd, 'ean')}'
                        f'{kesia_get(jd, 'description')[:32]}'
                        f'{kesia_get(jd, 'quantity')}'
                        f'{kesia_get(jd, 'achat_ht')}'
                        )
            #format values
            p = re.compile(r'\w+')
            product_providername = kesia_get(jd, 'provider')
            if product_providername is not None:
                product_provider, created = Provider.objects.get_or_create(
                name=providername,
                code=str(providername).replace(' ', '')[:3].upper())
                if created:
                    product_provider.save()

            code_art = kesia_get(jd, 'code_art')
            if code_art is not None:
                code_art = str(kesia_get(jd, 'code_art')).replace(provider.code, '')
                code_art = ''.join(p.findall(code_art)).upper()
                code_art = f'{provider.code}{code_art}'

            ean = ''.join(p.findall(str(kesia_get(jd, 'ean')))).upper()
            description = kesia_get(jd, 'description')[:32]
            quantity = int(float(str(kesia_get(jd, 'quantity')).replace(',', '.')))*operator
            try:
                achat_ht = float(
                    re.search(
                        r'([0-9]+.?[0-9]+)', str(kesia_get(jd, 'achat_ht')).replace(',', '.')
                        ).group(1)
                    )
            except:
                  achat_ht = float(str(kesia_get(jd, 'achat_ht')).replace(',', '.'))

            # get or create product
            try:
                if ean.isdigit():
                    product = Product.objects.get(ean=ean)
                else:
                    raise Product.DoesNotExist('EAN is not a digit')
            except Product.DoesNotExist:
                try:
                    if code_art is not None:
                        product = Product.objects.get(code_art=code_art)
                    else:
                        raise Product.DoesNotExist('No code article')
                except Product.DoesNotExist:
                    logger.debug("Create object")
                    product = Product.objects.create(description=description)
                    if product_providername is not None:
                        product.provider = product_provider
                    else:
                        product_provider = provider    
                    if code_art is None:
                        code_art = f'{provider.code}{product.id}'
                        logger.debug("Generate MultiCode")
                        product.multicode_generated = True

                    product.multicode = code_art
                    if ean.isdigit():
                        product.ean = ean
                        product.multicode = ean

            if product.achat_ht != achat_ht:
                logger.debug("Product has changed")
                product.has_changed=True
            else:
                product.has_changed=False
            product.achat_ht=achat_ht
            product.save()
            item_count += 1
            logger.debug(f'product {product.description} saved ! {item_count}/{len(json_data)}')



            transaction = Transaction.objects.create(
                product=product,
                quantity=quantity
            )
            transaction.save()
            logger.debug(f'transaction saved !')
            delivery.transactions.add(transaction)
            delivery.providers.add(product.provider)
        except Exception as e:
            return_obj['error_list'].append(f'{e}')
            logger.error(f'{e}')

    if not return_obj['error_list']:
        delivery.save()
        return_obj['delivery'] = delivery
    return return_obj

def kesia_get(jd, key):
    value = jd.get(key)
    if value is None:
        return jd.get(settings.KESIA2_COLUMNS_NAME.get(key))
    return value
