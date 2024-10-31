import re

from inventory.models import Product, Transaction
from provider.models import Provider
from delivery.models import Delivery


def json_to_db(providername, json_data, inventory, operator=1):
    # format return obj
    delivery_obj = Delivery.objects.create(inventory_name=inventory.name)
    return_obj = {'delivery_obj': delivery_obj, 'error_list': []}
    
    # get or create provider
    provider, created = Provider.objects.get_or_create(
        name=providername,
        code=str(providername).replace(' ', '')[:3].upper())
    provider.save()

    for jd in json_data:
        try:
            #format values
            p = re.compile('\w+')
            code_art = str(jd.get('code_art')).replace(provider.code, '')
            code_art = ''.join(p.findall(code_art)).upper()
            ean = ''.join(p.findall(str(jd.get('ean')))).upper()
            description = jd.get('description')
            quantity = int(jd.get('quantity'))*operator
            achat_brut = float(re.search(r'([0-9]+.?[0-9]+)', str(jd.get('achat_brut'))).group(1))

            # get or create product
            try:
                if ean.isdigit():
                    product = Product.objects.get(ean=ean)
                else:
                    raise Product.DoesNotExist('EAN is not a digit')    
            except Product.DoesNotExist:
                try:
                    if code_art is not None:
                        product = Product.objects.get(code_art=f'{provider.code}{code_art}')
                    else:
                        raise Product.DoesNotExist('No code article')         
                except Product.DoesNotExist:
                    product = product = Product.objects.create(
                        fournisseur=provider,
                        description=description)
            product.quantity+=quantity       
            if product.achat_brut != achat_brut:
                product.has_changed=True
            else:
                product.has_changed=False    
            product.achat_brut=achat_brut
            # test #
            product.code_art = f'{provider.code}{code_art}'
            #      #
            product.save()
            transaction = Transaction.objects.create(
                product=product,
                quantity=quantity
            )
            transaction.save()
            delivery_obj.products.add(transaction)
            inventory.products.add(product)
            inventory.transaction_list.add(transaction)
        except Exception as e:
            return_obj['error_list'].append(f'{e}')
    inventory.save()
    delivery_obj.save()
    return_obj['delivery_obj'] = delivery_obj
    return return_obj