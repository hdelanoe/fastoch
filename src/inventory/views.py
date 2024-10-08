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
from .forms import FileForm, QuestionForm, ProductForm
from inventory.models import Inventory, Product, Provider, StockTransaction, Kesia2_column_names
from backup.models import Backup


@login_required
def inventory_view(request, id=None, response=0, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    inventory_list = Inventory.objects.all()
    context = {
        "inventory": inventory_obj,
        "inventory_list": inventory_list,
        "columns": Kesia2_column_names.values(),
        "response": response,
        "products": inventory_obj.products.all(),

        
    }
    return render(request, "inventory/inventory.html", context) 

@login_required
def add_from_pdf(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            pdf_path = fs.path(filename)
            pages = convert_from_path(pdf_path, 2000, jpegopt='quality', use_pdftocairo=True, size=(None,1080))
            inventory = Inventory.objects.get(id=id)
            api = Mistral_API()
            image_content = []
            try:
                for count, page in enumerate(pages):
                    page.save(f'{settings.MEDIA_ROOT}/pdf{count}.jpg', 'JPEG')
                    jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                    image_content.append(format_content_from_image_path(jpg_path))
                try:
                    json_data = api.extract_json_from_image(image_content)
                    print(json_data.get('fournisseur'))
                    print(json_data.get('produits'))
                    error_list = json_to_db(json_data.get('fournisseur'), json_data.get('produits'), inventory)
                    if not error_list:
                        messages.success(request, "Your inventory has been updated.")
                    else:
                        messages.error(request, f'Error while extracting : {error_list}')
                except Exception as e:
                    messages.error(request, f'error while extracting {e}')
                for count, page in enumerate(pages):
                    jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                    fs.delete(jpg_path)

            except Exception as e:
                messages.error(request, f'error while parsing {e}')
            fs.delete(pdf_path)
        except Exception as e:
            messages.error(request, f'error while saving {e}')
    return redirect(reverse("inventory", args=[id, 0]))

@login_required
def add_from_xml(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            xml_path = fs.path(filename)
            inventory = Inventory.objects.get(id=id)
            df = pd.read_xml(xml_path)
            json_data = df.to_json(orient='records')
            error_list = json_to_db(json_data, inventory)
            if not error_list:
                messages.success(request, "Your inventory has been updated.")
            else:
                messages.error(request, f'Error while extracting : {error_list}')
        except Exception as e:
                messages.error(request, f'error while parsing {e}')
        fs.delete(xml_path)
    return redirect(reverse("inventory", args=[id, 0]))

@login_required
def add_from_csv(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            csv_path = fs.path(filename)
            inventory = Inventory.objects.get(id=id)
            df = pd.read_csv(csv_path)
            json_data = df.to_json(orient='records')
            error_list = json_to_db(json_data, inventory)
            if not error_list:
                messages.success(request, "Your inventory has been updated.")
            else:
                messages.error(request, f'Error while extracting : {error_list}')
        except Exception as e:
                messages.error(request, f'error while parsing {e}')
        fs.delete(csv_path)
    return redirect(reverse("inventory", args=[id, 0]))

@login_required
def remove_from_pdf(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            pdf_path = fs.path(filename)
            pages = convert_from_path(pdf_path, 800, jpegopt='quality', use_pdftocairo=True, size=(None,1080))
            inventory = Inventory.objects.get(id=id)
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
                    messages.error(request, f'error while extracting {e}')
                error_list = json_to_db(json_data.get('fournisseur'), json_data.get('produits'), inventory, -1)
                if not error_list:
                    messages.success(request, "Your inventory has been updated.")
                else:
                    messages.error(request, f'Erreur dans le parsing json : {error_list}')
                for count, page in enumerate(pages):
                    jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                    fs.delete(jpg_path)

            except Exception as e:
                messages.error(request, f'error while parsing {e}')
            fs.delete(pdf_path)
        except Exception as e:
            messages.error(request, f'error while saving {e}')
    return redirect(reverse("inventory", args=[id, 0]))

@login_required
def remove_from_xml(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            xml_path = fs.path(filename)
            inventory = Inventory.objects.get(id=id)
            df = pd.read_xml(xml_path)
            json_data = df.to_json(orient='records')
            error_list = json_to_db(json_data, inventory, -1)
            if not error_list:
                messages.success(request, "Your inventory has been updated.")
            else:
                messages.error(request, f'Erreur dans le parsing json : {error_list}')
        except Exception as e:
                messages.error(request, f'error while parsing {e}')
        fs.delete(xml_path)
    return redirect(reverse("inventory", args=[id, 0]))

@login_required
def remove_from_csv(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            csv_path = fs.path(filename)
            inventory = Inventory.objects.get(id=id)
            df = pd.read_csv(csv_path)
            json_data = df.to_json(orient='records')
            error_list = json_to_db(json_data, inventory, -1)
            if not error_list:
                messages.success(request, "Your inventory has been updated.")
            else:
                messages.error(request, f'Error while extracting : {error_list}')
        except Exception as e:
                messages.error(request, f'error while parsing {e}')
        fs.delete(csv_path)
    return redirect(reverse("inventory", args=[id, 0]))

def json_to_db(json_provider, json_products, inventory, operator=1):
    error_list = []
    pat = re.compile('([0-9]+.?[0-9]+)')
    n_tva = str(json_provider.get('n_tva')).replace(' ', '')
    try:
        provider = Provider.objects.get(n_tva=n_tva)
    except Provider.DoesNotExist:
        provider = Provider.objects.create(
            name=json_provider.get('name'),
            n_tva=json_provider.get('n_tva')
        )
    provider.save()
    for jd in json_products:
        try:
            ean = str(jd.get('ean')).replace(' ', '')
            achat_brut = float(re.search(r'([0-9]+.?[0-9]+)', str(jd.get('achat_brut'))).group(1))
            print(achat_brut)
            if not ean.isdigit():
                ean = None
                try:
                    product = Product.objects.get(description=jd.get('description'))
                    product.quantity+=int(jd.get('quantity'))*operator
                    product.achat_brut=achat_brut,
                    product.achat_net=achat_brut + (achat_brut*(provider.tva*0.01)),
                except Product.DoesNotExist:
                    product = Product.objects.create(
                    fournisseur=provider,
                    description=jd.get('description'),
                    quantity=int(jd.get('quantity'))*operator,
                    achat_brut=achat_brut,
                    achat_tva=provider.tva,
                    achat_net=achat_brut + (achat_brut*(provider.tva*0.01)),
                )
                except Exception as e:
                    error_list.append(f'{jd.get('description')} - {e}')
                        
            else:
                try:
                    product = Product.objects.get(ean=ean)
                    product.quantity+=int(jd.get('quantity'))*operator
                    product.achat_brut=achat_brut,
                    product.achat_net=achat_brut + (achat_brut*(provider.tva*0.01)),
                except Product.DoesNotExist: 
                    product = Product.objects.create(
                    fournisseur=provider,
                    ean=ean,
                    description=jd.get('description'),
                    quantity=int(jd.get('quantity'))*operator,
                    achat_brut=achat_brut,
                    achat_tva=provider.tva,
                    achat_net=achat_brut + (achat_brut*(provider.tva*0.01)),
                )
                except Exception as e:
                    error_list.append(f'{jd.get('description')} - {e}')    
            product.save()
            transaction = StockTransaction.objects.create(
                product=product,
                quantity=int(jd.get('quantity'))*operator
            )
            transaction.save()
            inventory.products.add(product)
            inventory.transaction_list.add(transaction)
        except Exception as e:
            error_list.append(f'{jd.get('description')} - {e}')
    inventory.save()
    return error_list


@login_required
def update_product(request, inventory=None, product=None, *args, **kwargs):
    if request.method == 'POST':
        product_obj = Product.objects.get(id=product)
        form = ProductForm(request.POST)
        product_obj.fournisseur = form.data['fournisseur']
        product_obj.description = form.data['description']
        product_obj.price_net = form.data['price_net']
        product_obj.price_tva = form.data['price_tva']
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