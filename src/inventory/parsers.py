import re

from django.conf import settings
from inventory.models import Product, Transaction
from provider.models import Provider
from delivery.models import Delivery



def json_to_db(providername, json_data, inventory, operator=1):
    # format return obj
    delivery = Delivery.objects.create(inventory=inventory)
    return_obj = {'delivery': delivery, 'error_list': []}

    # get or create provider
    provider, created = Provider.objects.get_or_create(
        name=providername,
        code=str(providername).replace(' ', '')[:3].upper())
    if created:
        provider.save()

    for jd in json_data:
        try:
            #format values
            p = re.compile('\w+')
            code_art = kesia_get(jd, 'code_art')
            if code_art is not None:
                code_art = str(kesia_get(jd, 'code_art')).replace(provider.code, '')
                code_art = ''.join(p.findall(code_art)).upper()
                code_art = f'{provider.code}{code_art}'

            ean = ''.join(p.findall(str(kesia_get(jd, 'ean')))).upper()
            description = kesia_get(jd, 'description')
            quantity = int(float(str(kesia_get(jd, 'quantity')).replace(',', '.')))*operator
            achat_brut = float(
                re.search(
                    r'([0-9]+.?[0-9]+)', str(kesia_get(jd, 'achat_brut')).replace(',', '.')
                    ).group(1)
                )

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
                    product = Product.objects.create(
                        fournisseur=provider,
                        description=description)
                    if code_art is None:
                        code_art = f'{provider.code}{product.id}'
                        product.multicode_generated = True
                    product.code_art = code_art
                    product.multicode = code_art
                    if ean.isdigit():
                        product.ean = ean
                        product.multicode = ean

            if product.achat_brut != achat_brut:
                product.has_changed=True
            else:
                product.has_changed=False
            product.achat_brut=achat_brut
            product.save()


            transaction = Transaction.objects.create(
                product=product,
                quantity=quantity
            )
            transaction.save()
            delivery.transactions.add(transaction)
            delivery.providers.add(product.fournisseur)
        except Exception as e:
            return_obj['error_list'].append(f'{e}')

    if not return_obj['error_list']:
        delivery.save()
        return_obj['delivery'] = delivery
    return return_obj

def kesia_get(jd, key):
    value = jd.get(key)
    if value is None:
        return jd.get(settings.KESIA2_COLUMNS_NAME.get(key))
    return value
