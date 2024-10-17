import os
from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import reverse
import pandas as pd
import re
from pdf2image import convert_from_path

from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from helpers.mistral import Mistral_API, Codestral_Mamba, format_content_from_image_path
from .forms import ImportForm, QuestionForm, ProductForm
from inventory.models import Inventory, Product, StockTransaction, Kesia2_column_names
from provider.models import Provider
from backup.models import Backup
from delivery.models import Delivery
from delivery.views import last_delivery_view

from dashboard.views import init_context



@login_required
def inventory_view(request, id=None, response=0, *args, **kwargs):
    context = init_context()
    inventory_obj = Inventory.objects.get(id=id)
    context["inventory"] = inventory_obj
    context["columns"] = Kesia2_column_names.values()
    context["response"] = response
    context["products"] = inventory_obj.products.all()
    return render(request, "inventory/inventory.html", context) 

@login_required
def move_from_file(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            form = ImportForm(request.POST)
            uploaded_file = request.FILES['document']
            providername = form.data['provider']
            move_type = int(form.data['move_type'])
            filename, file_extension = os.path.splitext(uploaded_file.name)
            print(file_extension)
            if file_extension == ".pdf" or file_extension == ".xml" or file_extension == ".csv":
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_path = fs.path(filename)
                inventory = Inventory.objects.get(id=id)

                if file_extension == ".pdf":
                    pages = convert_from_path(file_path, 2000, jpegopt='quality', use_pdftocairo=True, size=(None,1080))
                    api = Mistral_API()
                    image_content = []
                    delivery_obj = Delivery.objects.create()
                    try:
                        for count, page in enumerate(pages):
                            page.save(f'{settings.MEDIA_ROOT}/pdf{count}.jpg', 'JPEG')
                            jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                            image_content.append(format_content_from_image_path(jpg_path))
                        try:
                            json_data = api.extract_json_from_image(image_content)
                        except Exception as e:
                            messages.error(request, f'error while extracting {e}')
                        for count, page in enumerate(pages):
                            jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                            fs.delete(jpg_path)
                    except Exception as e:
                        messages.error(request, f'error while parsing {e}')
                else:
                    if file_extension == ".xml":
                        df = pd.read_xml(file_path)
                    if file_extension == ".csv":
                        df = pd.read_csv(file_path)  
                    json_data = df.to_json(orient='records')
                return_obj = json_to_db(providername, json_data, inventory, move_type)
                error_list = return_obj.get('error_list')
                delivery_obj = return_obj.get('delivery_obj')
                if not error_list:
                    messages.success(request, "Your inventory has been updated.")
                else:
                    messages.error(request, f'Error while extracting : {error_list}')     
                fs.delete(file_path)
                return redirect(reverse(last_delivery_view, args=[delivery_obj.id]))
            else:
                messages.error(request, f'Les fichiers de type {file_extension} ne sont pas pris en charge.')  
        except Exception as e:
            messages.error(request, f'error while saving {e}')
    return redirect(reverse("inventory", args=[id, 0]))

def json_to_db(providername, json_data, inventory, operator=1):
    delivery_obj = Delivery.objects.create(inventory_name=inventory.name)
    return_obj = {
        'delivery_obj': delivery_obj, 
        'error_list': []
        }
    try:
        provider = Provider.objects.get(name=providername)
    except Provider.DoesNotExist:
        provider = Provider.objects.create(
            name=providername,
            code=str(providername).replace(' ', '')[:3].upper(),
        )
    provider.save()
    for jd in json_data:
        try:
            ean = str(jd.get('ean')).replace(' ', '')
            if not ean.isdigit():
                ean = None
                try:
                    product = Product.objects.get(description=jd.get('description'))
                    product.quantity+=int(jd.get('quantity'))*operator
                    product.achat_brut= float(re.search(r'([0-9]+.?[0-9]+)', str(jd.get('achat_brut'))).group(1))
                    product.has_changed = True
                
                    #product.achat_net=round(achat_brut + (achat_brut*(provider.tva*0.01)), 2),
                except Product.DoesNotExist:
                    product = Product.objects.create(
                    fournisseur=provider,
                    description=jd.get('description'),
                    quantity=int(jd.get('quantity'))*operator,
                    achat_brut= float(re.search(r'([0-9]+.?[0-9]+)', str(jd.get('achat_brut'))).group(1))
                    #achat_net=round(achat_brut + (achat_brut*(provider.tva*0.01)), 2),
                )
                except Exception as e:
                    return_obj['error_list'].append(f'{'ligne 237'} - {e}')
                        
            else:
                try:
                    product = Product.objects.get(ean=ean)
                    product.quantity+=int(jd.get('quantity'))*operator
                    product.achat_brut= float(re.search(r'([0-9]+.?[0-9]+)', str(jd.get('achat_brut'))).group(1))
                    product.has_changed = True
                    #product.achat_net=round(achat_brut + (achat_brut*(provider.tva*0.01)), 2),
                except Product.DoesNotExist: 
                    product = Product.objects.create(
                    fournisseur=provider,
                    ean=ean,
                    description=jd.get('description'),
                    quantity=int(jd.get('quantity'))*operator,
                    achat_brut= float(re.search(r'([0-9]+.?[0-9]+)', str(jd.get('achat_brut'))).group(1))
                    #achat_net=round(achat_brut + (achat_brut*(provider.tva*0.01)), 2),
                )
                except Exception as e:
                    return_obj['error_list'].append(f'{'ligne 257'} - {e}')    
            product.save()
            transaction = StockTransaction.objects.create(
                product=product,
                quantity=int(jd.get('quantity'))*operator
            )
            transaction.save()
            delivery_obj.products.add(product)
            inventory.products.add(product)
            inventory.transaction_list.add(transaction)
        except Exception as e:
            return_obj['error_list'].append(f'{'ligne 268'} - {e}')
        #finally:
        #    None
    inventory.save()
    delivery_obj.save()
    return_obj['delivery_obj'] = delivery_obj
    return return_obj


@login_required
def update_product(request, inventory=None, product=None, *args, **kwargs):
    if request.method == 'POST':
        product_obj = Product.objects.get(id=product)
        form = ProductForm(request.POST)
        product_obj.description = form.data['description']
        product_obj.price_net = form.data['price_net']
        product_obj.save()
    return redirect(reverse("inventory", args=[id, 1]))    

@login_required
def ask_question(request, id=None, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    if request.method == 'POST':
        api = Codestral_Mamba()
        form = QuestionForm(request.POST)
        df = pd.DataFrame([x.as_Kesia2_dict() for x in inventory_obj.products.all()])
        inventory_obj.last_response = api.chat(form.data['question'], df)
        inventory_obj.save()
    print(inventory_obj.last_response)    
    return redirect(reverse("inventory", args=[id, 1]))

@login_required
def backup_inventory(request, id=None, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    save_backup(inventory_obj)
    messages.success(request, "Your inventory has been backup.")
    return redirect(reverse("inventory", args=[id, 0]))

@login_required
def export_inventory(request, id=None, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    backup = save_backup(inventory_obj)
    columns = Kesia2_column_names.values()
    df = pd.DataFrame([p.as_Kesia2_dict() for p in inventory_obj.products.all()], columns = columns,)
    file_path = f'{settings.MEDIA_ROOT}/{backup.inventory_name}_{str(backup.date_creation)[:10]}.xlsx'
    df.to_excel(file_path, index=False)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

def save_backup(inventory):
    backup = Backup(
        inventory_name=inventory.name,
        products_backup = pd.DataFrame([x.as_Kesia2_dict() for x in inventory.products.all()]),
        transactions_backup = pd.DataFrame([x.as_dict() for x in inventory.transaction_list.all()])
    )
    backup.save()
    return(backup)