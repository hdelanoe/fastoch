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

def file_to_json(uploaded_file, file_extension):
    return_obj = {'json': {}, 'error_list': {}}
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

def json_to_delivery(providername, json_data, inventory, operator=1):
    # format return obj
    delivery = Delivery.objects.create(inventory=inventory)
    return_obj = {'delivery': delivery, 'error_list': []}
    item_count = 0

    provider = get_or_create_provider(providername)

    for jd in json_data:
        try:
            values=format_json_values(jd, provider, operator)
            product=get_or_create_product(values)

            item_count += 1
            logger.debug(f'product {product.description} saved ! {item_count}/{len(json_data)}')

            transaction = Transaction.objects.create(
                product=product,
                quantity=values.get('quantity')
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

def json_to_import(json_data, inventory):
    # format return obj
    return_obj = {'inventory': inventory, 'error_list': []}
    item_count = 0

    provider = get_or_create_provider(inventory.name)

    for jd in json_data:
        try:
            values = format_json_values(jd, provider)
            product=get_or_create_product(values)

            item_count += 1
            logger.debug(f'product {product.description} saved ! {item_count}/{len(json_data)}')

            inventory.add(product)
        except Exception as e:
            return_obj['error_list'].append(f'{e}')
            logger.error(f'{e}')

    if not return_obj['error_list']:
        inventory.save()
        return_obj['inventory'] = inventory
    return return_obj

def get_or_create_provider(providername):
    provider, created = Provider.objects.get_or_create(
        name=providername,
        code=str(providername).replace(' ', '')[:3].upper())
    if created:
        provider.save()
    return provider

def format_json_values(jd, provider, operator):
    values = {'provider': {}, 
              'code_art': {},
              'ean': {},
              'description': {},
              'quantity': {},
              'achat_ht': {},
              }
    logger.debug(
                f'{kesia_get(jd, 'provider')}'
                f'{kesia_get(jd, 'code_art')}'
                f'{kesia_get(jd, 'ean')}'
                f'{kesia_get(jd, 'description')[:32]}'
                f'{kesia_get(jd, 'quantity')}'
                f'{kesia_get(jd, 'achat_ht')}'
                )
    
    p = re.compile(r'\w+')
    product_providername = kesia_get(jd, 'provider')
    if product_providername is not None:
        product_provider, created = Provider.objects.get_or_create(
        name=provider.name,
        code=str(provider.name).replace(' ', '')[:3].upper())
        if created:
            product_provider.save()
    else:
        product_provider=provider        

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

    values['provider']=provider     
    values['code_art']=code_art     
    values['ean']=ean     
    values['description']=description     
    values['quantity']=quantity     
    values['achat_ht']=achat_ht   
    return values  

def get_or_create_product(values):
    try:
        if values.get('ean').isdigit():
            product = Product.objects.get(ean=values.get('ean'))
        else:
            raise Product.DoesNotExist('EAN is not a digit')
    except Product.DoesNotExist:
        try:
            if values.get('code_art') is not None:
                product = Product.objects.get(code_art=values.get('code_art'))
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
