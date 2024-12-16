import logging
import re
import json
import pandas as pd

from django.core.files.storage import FileSystemStorage
from django.conf import settings
from inventory.models import Product, iProduct
from provider.models import Provider
from delivery.models import Delivery

from helpers.mistral import Mistral_PDF_API, format_content_from_image_path
from pdf2image import convert_from_path

logger = logging.getLogger('fastoch')

def file_to_json(uploaded_file, file_extension):
    return_obj = {'json': {}, 'error_list': {}}
    fs = FileSystemStorage()
    file = fs.save(uploaded_file.name, uploaded_file)
    file_path = fs.path(file)
    if file_extension == ".pdf":
        pages = convert_from_path(file_path, 2000, jpegopt='quality', use_pdftocairo=True, size=(None,1080))
        api = Mistral_PDF_API()
        image_content = []
        try:
            for count, page in enumerate(pages):
                page.save(f'{settings.MEDIA_ROOT}/pdf{count}.jpg', 'JPEG')
                jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                image_content.append(format_content_from_image_path(jpg_path))
            try:
                return_obj['json'] = api.extract_json_from_image(image_content)
            except Exception as e:
                logger.error(f"Error while extracting data from pdf with mistral - {e}")
                return_obj['error_list'] = "Erreur lors de la lecture du .pdf"
            for count, page in enumerate(pages):
                jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                fs.delete(jpg_path)
        except Exception as e:
            logger.error(f"Error while saving file - {e}")
            return_obj['error_list'] = "Erreur lors de la lecture du .pdf"
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


    for jd in json_data:
        try:
            values=format_json_values(jd, provider, operator)
            product=get_or_create_product(values)

            iproduct = iProduct.objects.create(product=product, 
                                               quantity=values.get('quantity'),
                                               container_name=str(delivery.date_time))
            iproduct.save()
            logger.debug(f'iproduct from {product.description} created !')
            item_count += 1
        except Exception as e:
            return_obj['error_list'].append(f'product {values.get('description')} : {e}')
            logger.error(f'product {values.get('description')} : {e}')

    delivery.save()
    return_obj['delivery'] = delivery
    return_obj['report'] = f'product {product.description} saved ! {item_count}/{len(json_data)}'
    logger.debug(return_obj['report'])    
    return return_obj

def json_to_import(json_data, inventory):
    # format return obj
    return_obj = {'inventory': inventory, 'error_list': []}
    item_count = 0
    saved_item = 0

    provider = get_or_create_provider(inventory.name)

    for jd in json_data:
        try:
            values = format_json_values(jd, provider)
            product = get_or_create_product(values)
            if not product:
                raise Exception('no products')

            item_count += 1
            logger.debug(f'product {product.description} saved ! {item_count}/{len(json_data)}')

            iproduct, created = iProduct.objects.get_or_create(container_name=inventory.name,
                                                      product=product)
            iproduct.quantity+=values.get('quantity')
            iproduct.save()
            saved_item += 1
        except ValueError as ex:
             return_obj['error_list'].append(f'Erreur lors de l\'import de {values.get('description')} : {ex}\n')
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            return_obj['error_list'].append(f'product {values.get('description')} : {ex}')
            logger.error(f'{message}')

    inventory.save()

    logger.info(f'{saved_item} produit(s) sur {len(json_data)} importé(s).')
    return_obj['inventory'] = inventory
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
                f'{kesia_get(jd, 'provider')} '
                f'{kesia_get(jd, 'code_art')} '
                f'{kesia_get(jd, 'ean')} '
                f'{kesia_get(jd, 'description')[:64]} '
                f'{kesia_get(jd, 'quantity')} '
                f'{kesia_get(jd, 'achat_ht')} '
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

    ean = ''.join(p.findall(str(kesia_get(jd, 'ean')))).upper()
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
    try:
        if values.get('ean').isdigit():
            product = Product.objects.get(multicode=values.get('ean'))
            product.is_new=False
        else:
            raise Product.DoesNotExist('EAN is not a digit')
    except Product.DoesNotExist:
        try:
            if values.get('code_art') is not None:
                product = Product.objects.get(multicode=values.get('code_art'))
                product.is_new=False
            else:
                raise Product.DoesNotExist('No code article')
        except Product.DoesNotExist:
            logger.debug("Create object")
            product = Product.objects.create(
                description=values.get('description'),
                provider=values.get('provider'))

            if  values.get('ean').isdigit():
                product.ean = values.get('ean')
                product.multicode = values.get('ean')
            else:
                logger.debug("Generate MultiCode")
                if values.get('code_art'):
                    product.multicode = values.get('code_art')
                else:
                    product.multicode = f'{values.get('provider').code}{product.id}'
                product.multicode_generated = True

    if product.achat_ht != values.get('achat_ht'):
        logger.debug("Product achat_ht has changed")
        product.achat_ht=values.get('achat_ht')
        product.has_changed=True
    else:
        product.has_changed=False
    product.save()
    return product

def kesia_get(jd, key):
    value = jd.get(key)
    if value is None:
        return jd.get(settings.KESIA2_COLUMNS_NAME.get(key))
    return value
