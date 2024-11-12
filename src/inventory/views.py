import json
import os
from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import reverse
import pandas as pd
from pdf2image import convert_from_path

from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from helpers.mistral import Mistral_API, Codestral_Mamba, format_content_from_image_path
from .forms import ImportForm, QuestionForm, ProductForm
from .parsers import json_to_db
from inventory.models import Inventory, Product
from backup.models import Backup

from dashboard.views import init_context



@login_required
def inventory_view(request, id=None, response=0, *args, **kwargs):
    context = init_context()
    inventory = Inventory.objects.get(id=id)
    context["inventory"] = inventory
    context["columns"] = settings.KESIA2_COLUMNS_NAME.values()
    context["response"] = response
    context["products"] = inventory.products.all()
    return render(request, "inventory/inventory.html", context)

@login_required
def move_from_file(request, id=None, *args, **kwargs):
    redirect_url = reverse("inventory", args=[id, 0])
    if request.method == 'POST':
        try:
            form = ImportForm(request.POST)
            uploaded_file = request.FILES['document']
            providername = form.data['provider']
            move_type = int(form.data['move_type'])
            filename, file_extension = os.path.splitext(uploaded_file.name)
            if file_extension == ".pdf" or file_extension == ".xml" or file_extension == ".xlsx" or file_extension == ".csv":
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_path = fs.path(filename)
                inventory = Inventory.objects.get(id=id)

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
                            messages.error(request, f'error while extracting {e}')
                        for count, page in enumerate(pages):
                            jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                            fs.delete(jpg_path)
                    except Exception as e:
                        messages.error(request, f'error while parsing {e}')
                else:
                    if file_extension == ".xlsx":
                        df = pd.read_excel(file_path)
                    if file_extension == ".xml":
                        df = pd.read_xml(file_path, encoding='utf-8')
                    if file_extension == ".csv":
                        df = pd.read_csv(file_path, encoding='utf-8')    
                    json_data = json.loads(df.to_json(orient='records'))
                    print(json_data)
                return_obj = json_to_db(providername, json_data, inventory, move_type)
                error_list = return_obj.get('error_list')
                delivery = return_obj.get('delivery')
                if not error_list:
                    messages.success(request, "Livraison bien enregistrée.")
                    redirect_url = reverse('last_delivery', args=[delivery.id])
                else:
                    messages.error(request, f'Error while extracting : {error_list}')
                fs.delete(file_path)
            else:
                messages.error(request, f'Les fichiers de type {file_extension} ne sont pas pris en charge.')
        except Exception as e:
            messages.error(request, f'error while saving {e}')
    return redirect(redirect_url)




@login_required
def update_product(request, inventory=None, product=None, *args, **kwargs):
    if request.method == 'POST':
        product_obj = Product.objects.get(id=product)
        form = ProductForm(request.POST)
        product_obj.description = form.data['description']
        product_obj.price_net = form.data['price_net']
        product_obj.save()
    return redirect(reverse("inventory", args=[inventory, 0]))

@login_required
def delete_product(request, inventory=None, product=None, *args, **kwargs):
    if request.method == 'POST':
        product_obj = Product.objects.get(id=product)
        product_obj.delete()
    return redirect(reverse("inventory", args=[inventory, 0]))

@login_required
def ask_question(request, id=None, *args, **kwargs):
    inventory = Inventory.objects.get(id=id)
    if request.method == 'POST':
        api = Codestral_Mamba()
        form = QuestionForm(request.POST)
        df = pd.DataFrame([x.as_Kesia2_dict() for x in inventory.products.all()])
        inventory.last_response = api.chat(form.data['question'], df)
        inventory.save()
    print(inventory.last_response)
    return redirect(reverse("inventory", args=[id, 1]))


@login_required
def import_inventory(request, id=None, *args, **kwargs):
    redirect_url = reverse("inventory", args=[id, 0])
    if request.method == 'POST':
        try:
            form = ImportForm(request.POST)
            uploaded_file = request.FILES['document']
            providername = form.data['provider']
            move_type = int(form.data['move_type'])
            filename, file_extension = os.path.splitext(uploaded_file.name)
            if file_extension == ".xml" or file_extension == ".xlsx" or file_extension == ".csv":
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_path = fs.path(filename)
                inventory = Inventory.objects.get(id=id)

                if file_extension == ".xml" or file_extension == ".xlsx":
                    df = pd.read_xml(file_path, encoding='utf-8')
                if file_extension == ".csv":
                    df = pd.read_csv(file_path, encoding='utf-8')
                json_data = json.loads(df.to_json(orient='records'))
                return_obj = json_to_db(providername, json_data, inventory, move_type)
                error_list = return_obj.get('error_list')
                delivery = return_obj.get('delivery')
                if not error_list:
                    for p in inventory.products.all():
                        p.delete()
                    for t in delivery.transactions.all():
                        inventory.products.add(t.product)
                    inventory.save()
                    messages.success(request, "L'import est un succés. L'inventaire est mis a jour.")
                    redirect_url = reverse('last_delivery', args=[delivery.id])
                else:
                    messages.error(request, f'Error while extracting : {error_list}')
                fs.delete(file_path)
            else:
                messages.error(request, f'Les fichiers de type {file_extension} ne sont pas pris en charge.')
        except Exception as e:
            messages.error(request, f'error while saving {e}')
    return redirect(redirect_url)


@login_required
def export_inventory(request, id=None, *args, **kwargs):
    inventory = Inventory.objects.get(id=id)
    backup = save_backup(inventory)
    df = pd.DataFrame.from_dict(
        [p.as_Kesia2_dict() for p in inventory.products.all()],
        orient='columns'
        )
    file_path = f'{settings.MEDIA_ROOT}/{inventory.name}_{str(backup.date_creation)[:10]}.xml'
    df.to_excel(file_path, index=False)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def backup_inventory(request, id=None, *args, **kwargs):
    inventory = Inventory.objects.get(id=id)
    save_backup(inventory, Backup.BackupType.MANUAL)
    messages.success(request, "Your inventory has been backup.")
    return redirect(reverse("inventory", args=[id, 0]))

def save_backup(inventory, type=Backup.BackupType.AUTO):
    backup = Backup(
        inventory=inventory,
        products_backup = pd.DataFrame([x.as_Kesia2_dict() for x in inventory.products.all()]).to_json(orient='table'),
        transactions_backup = pd.DataFrame([x.as_dict() for x in inventory.transaction_list.all()]).to_json(orient='table'),
        backup_type = type
    )
    backup.save()
    return(backup)
