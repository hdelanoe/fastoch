import logging
import os
import re
import json
import pandas as pd

from django.core.files.storage import FileSystemStorage
from django.conf import settings
from inventory.models import Product, iProduct
from provider.models import Provider
from delivery.models import Delivery
from settings.models import Settings

from helpers.mistral import Mistral_PDF_API, Mistral_Nemo_API, format_content_from_image_path
from helpers.paddlepaddle import table_recognition
import helpers.preprocesser

logger = logging.getLogger('fastoch')

def file_to_json(uploaded_file, file_extension):
    return_obj = {'json': {}, 'error_list': {}}
    fs = FileSystemStorage()
    file = fs.save(uploaded_file.name, uploaded_file)
    file_path = fs.path(file)
    if file_extension == ".pdf" or file_extension == ".png" or file_extension == ".heic":
        image_content = []
        table = ""
        if file_extension == ".pdf":
            pages = helpers.preprocesser.process_png(file_path)
            try:
                for count, page in enumerate(pages):
                    png_path = f'{settings.MEDIA_ROOT}/table{count}.png'
                    page.save(png_path, 'PNG')
                    logger.debug('- png saved -')

                    #helpers.preprocesser.image_processing(png_path)
                    #logger.debug('- png processed -')
                    table_recognition(png_path)
                    logger.debug('- html saved -')
                    try:
                        xlsx_path=f'{settings.MEDIA_ROOT}/table{count}/table{count}.xlsx'
                        csv_path = helpers.preprocesser.xlsx_to_csv(xlsx_path)
                        f = open(csv_path, "r")
                        table += f.read()
                        f.close()
                        os.remove(xlsx_path)
                        os.remove(csv_path)
                    except Exception as e :
                        logger.warning(f"Error while analyzing table{count} : {e}")
                    #text += helpers.preprocesser.tesseract(png_path)
                    #path = fs.path(png_path)
                    #image_content.append(format_content_from_image_path(path))
            except Exception as e:
                logger.error(f"Error while saving file - {e}")
                return_obj['error_list'] = "Erreur lors de la lecture du .pdf"
        else:
            if file_extension == ".heic":
                png_path = helpers.preprocesser.convert_heic_to_png(uploaded_file.name, file_path)
            else:
                png_path = file_path
            if not png_path:
                return_obj['error_list'] = f"Erreur lors de la conversion du fichier HEIC."
                return (return_obj)
            else:
                helpers.preprocesser.image_processing(png_path)
                text += helpers.preprocesser.tesseract(png_path)
                image_content.append(format_content_from_image_path(png_path))
        try:
            #api = Mistral_PDF_API()
            api = Mistral_Nemo_API()
            return_obj['json'] = api.extract_json_from_html(table)
            #first_json = api.extract_json_from_image(image_content)
            #logger.debug('first_json ok')
            #return_obj['json'] = api.replace_ean_by_tesseract(first_json, text)
            #logger.debug('replace by tesseract ok')
            #return_obj['json'] = api.extract_json_from_image(image_content)
        except Exception as e:
            logger.error(f"Error while extracting data from pdf with mistral - {e}")
            return_obj['error_list'] = f'Erreur lors de la lecture du .pdf : {e}'
        if file_extension == ".pdf":
            for count, page in enumerate(pages):
                png_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.png')
                fs.delete(png_path)

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
            return_obj['error_list'] = f"Erreur lors de la lecture du {file_extension}"
        try:
            return_obj['json'] = json.loads(df.to_json(orient='records'))
        except Exception as e:
            logger.error(f"Error while loading df in json - {e}")
            return_obj['error_list'] = f"Erreur lors de la lecture du {file_extension}"
    fs.delete(file_path)
    return (return_obj)

def json_to_delivery(providername, json_data, operator=1):
    # format return obj
    provider = get_or_create_provider(providername)
    delivery = Delivery.objects.create(provider=provider)
    return_obj = {'delivery': delivery, 'error_list': [], 'report': ''}
    item_count = 0

    try:
        json_data = json_data['products']
    except:
        None
    for jd in json_data:
        try:
            values=format_json_values(jd, provider, operator)
            product=get_or_create_product(values)
            logger.debug(f'product {product} return by get_or_create')
            iproduct = iProduct.objects.create(product=product,
                                               quantity=values.get('quantity'),
                                               container_name=str(delivery.date_time))
            iproduct.save()
            logger.debug(f'iproduct from {product.description} created !')
            item_count += 1
        except (Exception, UnboundLocalError) as e:
            return_obj['error_list'].append(f"product {values.get('description')} : {e}")
            logger.error(f"product {values.get('description')} : {e}")

    delivery.save()
    return_obj['delivery'] = delivery
    return_obj['report'] = f'product {product.description} saved ! {item_count}/{len(json_data)}'
    logger.debug(return_obj['report'])
    return return_obj

def json_to_import(json_data, inventory):
    # format return obj
    return_obj = {'inventory': inventory, 'error_list': [], 'report': ''}
    item_count = 0
    saved_item = 0

    provider = get_or_create_provider(inventory.name)

    for jd in json_data:
        try:
            values = format_json_values(jd, provider)
            product = get_or_create_product(values)
            if not product:
                raise Exception('no products')

            # Remove is_new from import
            product.is_new = False
            product.save()


            # Remove is_new from import
            product.is_new = False
            product.save()


            item_count += 1
            logger.debug(f'product {product.description} saved ! {item_count}/{len(json_data)}')

            iproduct, created = iProduct.objects.get_or_create(container_name=inventory.name,
                                                      product=product)
            iproduct.quantity+=values.get('quantity')
            iproduct.save()
            saved_item += 1
        except ValueError as ex:
             return_obj['error_list'].append(f"Erreur lors de l\'import de {values.get('description')} : {ex}\n")
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            return_obj['error_list'].append(f"product {values.get('description')} : {ex}")
            logger.error(f'{message}')

    inventory.save()

    logger.info(f'{saved_item} produit(s) sur {len(json_data)} importé(s).')
    return_obj['inventory'] = inventory
    return_obj['report'] = f'product {product.description} saved ! {item_count}/{len(json_data)}'
    logger.debug(return_obj['report'])
    return return_obj


def format_json_values(jd, provider, operator=1):
    values = {'provider': {},
              'code_art': {},
              'ean': {},
              'description': {},
              'quantity': {},
              'achat_ht': {},
              }

    logger.debug(f'{provider.name}')
    logger.debug(
                f"{kesia_get(jd, 'provider')}"
                f"{kesia_get(jd, 'code_art')}"
                f"{kesia_get(jd, 'ean')} "
                f"{kesia_get(jd, 'description')[:64]}"
                f"{kesia_get(jd, 'quantity')}"
                f"{kesia_get(jd, 'achat_ht')}"
                )

    p = re.compile(r'\w+')
    product_providername = kesia_get(jd, 'provider')
    if product_providername is not None:
        product_provider=get_or_create_provider(product_providername)
    else:
        product_provider=provider

    code_art = kesia_get(jd, 'code_art')
    if code_art is not None:
        code_art = str(kesia_get(jd, 'code_art')).replace(provider.code, '')
        code_art = ''.join(p.findall(code_art)).upper()
        code_art = f'{provider.code}{code_art}'

    try:
        str_ean = str(int(float(kesia_get(jd, 'ean'))))
    except:
        str_ean = str(kesia_get(jd, 'ean'))
    ean = ''.join(p.findall(str_ean)).upper()
    description = kesia_get(jd, 'description')[:64]
    quantity = int(float(str(kesia_get(jd, 'quantity')).replace(',', '.')))*operator
    try:
        achat_ht = float(
            re.search(
                r'([0-9]+.?[0-9]+)', str(kesia_get(jd, 'achat_ht')).replace(',', '.')
                ).group(1)
            )
    except:
            achat_ht = float(str(kesia_get(jd, 'achat_ht')).replace(',', '.'))

    values['provider']=product_provider
    values['code_art']=code_art
    values['ean']=ean
    values['description']=description
    values['quantity']=quantity
    values['achat_ht']=achat_ht
    logger.debug(f'values {values}')
    return values

def get_or_create_provider(providername):
    rpro = re.compile(r'([A-z]+)')
    provider, created = Provider.objects.get_or_create(
        name=providername[:32],
        code=''.join(rpro.findall(str(providername)))[:4].upper()
    )
    if created:
        provider.save()
    return provider

def get_or_create_product(values):
    settings, created = Settings.objects.get_or_create(id=1)
    logger.debug('get_or_create')
    product = find_existant_product(values)
    logger.debug(f"Product returned from find_existant_product: {product}, type: {type(product)}")
    if product is None:
        logger.debug("Create object")
        product = Product.objects.create(
            description=values.get('description'),
            provider=values.get('provider'))

    if  validate_ean(values.get('ean')):
        product.ean = values.get('ean')
        if settings.erase_multicode is True:
            product.multicode = values.get('ean')
            product.multicode_generated = False
    else:
        if values.get('code_art') is not None:
            product.multicode = values.get('code_art')
            product.multicode_generated = False
        elif product.is_new:
            logger.debug("Generate MultiCode")
            product.multicode = f"{values.get('provider').code}{product.id}"
            product.multicode_generated = True

    if product.achat_ht != values.get('achat_ht') and product.is_new==False:
        logger.debug("Product achat_ht has changed")
        product.has_changed=True
        product.achat_ht=values.get('achat_ht')
    elif product.is_new:
        product.achat_ht=values.get('achat_ht')
    else:
        product.has_changed=False
    logger.debug(f'finale porudct : {product}')
    product.save()
    return product

def find_existant_product(values):
    ean = values.get('ean')
    code_art = values.get('code_art')
    if validate_ean(ean):
        result = find_ean(ean, code_art)
    else:
        result = find_multicode(code_art)

    logger.debug(f"find_existant_product returned: {result}")
    return result

def find_ean(ean, code_art):
    try:
        logger.debug(f"Trying to find product by ean: {ean}")
        return Product.objects.get(ean=ean)
    except:
        try:
            logger.debug(f"Trying to find product by multicode: {ean}")
            return Product.objects.get(multicode=ean)
        except:
            result = find_multicode(code_art)
            logger.debug(f"find_ean ultimately returned: {result}")
            return result

def find_multicode(code_art):
    try:
        if code_art is not None:
            logger.debug(f"Trying to find product by multicode: {code_art}")
            return Product.objects.get(multicode=code_art)
        else:
            logger.debug("No code_art provided")
            return None
    except:
        logger.debug(f"find_multicode returned None for code_art: {code_art}")
        return None

def validate_ean(ean):
    try:
        if len(ean) != 13 or not ean.isdigit():
            return False
    #checksum = sum((3 if i % 2 else 1) * int(x) for i, x in enumerate(ean[:-1]))
    #return (10 - (checksum % 10)) % 10 == int(ean[-1])
        return True
    except:
        return False

def kesia_get(jd, key):
    value = jd.get(key)
    if value is None:
        return jd.get(settings.KESIA2_COLUMNS_NAME.get(key))
    return value
