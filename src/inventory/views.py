import re
import os
import logging

from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import reverse
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from helpers.mistral import Codestral_Mamba
from .forms import ImportForm, QuestionForm
from .parsers import file_to_json, json_to_delivery, json_to_import
from inventory.models import Inventory, Product
from backup.models import Backup

from home.views import init_context

logger = logging.getLogger('fastoch')


@login_required
def inventory_view(request, id=None, response=0, *args, **kwargs):
    context = init_context()
    inventory = Inventory.objects.get(id=id)
    context["inventory"] = inventory
    context["columns"] = settings.INVENTORY_COLUMNS_NAME.values()
    context["response"] = response
    context["products"] = inventory.products.all()
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
            if file_extension == ".pdf" or file_extension == ".xml" or file_extension == ".xlsx" or file_extension == ".xls" or file_extension == ".csv":
                # Parsing file #
                return_obj = file_to_json(uploaded_file, file_extension)
                json_data = return_obj.get('json')
                error_list = return_obj.get('error_list')
                if error_list:
                    messages.error(request, error_list)
                    return redirect(reverse("inventory", args=[id, 0]))
                inventory = Inventory.objects.get(id=id)
                # Parsing json #
                return_obj = json_to_delivery(providername, json_data, inventory, move_type)
                error_list = return_obj.get('error_list')
                delivery = return_obj.get('delivery')
                if error_list:
                    messages.error(request, f'Error while extracting : {error_list}')
                else:
                    messages.success(request, "Livraison bien enregistrée.")
                return redirect(reverse('last_delivery', args=[delivery.id]))
            else:
                messages.error(request, f'Les fichiers de type {file_extension} ne sont pas pris en charge.')
        except Exception as e:
            messages.error(request, f'error while saving {e}')
    return redirect(reverse("inventory", args=[id, 0]))




@login_required
def update_product(request, inventory=None, product=None, *args, **kwargs):
    if request.method == 'POST':
        product_obj = Product.objects.get(id=product)
        product_obj.description = request.POST.get('description', product_obj.description)
        product_obj.quantity = request.POST.get('quantity', product_obj.quantity)
        product_obj.achat_ht = re.search(
                    r'([0-9]+.?[0-9]+)', str(request.POST.get('achat_ht', product_obj.achat_ht)).replace(',', '.')
                    ).group(1)

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
def import_inventory(request, *args, **kwargs):
    if request.method == 'POST':
        #try:
            uploaded_file = request.FILES['document']
            name = request.POST['name']
            filename, file_extension = os.path.splitext(uploaded_file.name)
            logger.debug(f"start parse {filename}")
            if file_extension == ".xml" or file_extension == ".xlsx" or file_extension == ".xls" or file_extension == ".csv":
                return_obj = file_to_json(uploaded_file, file_extension)
                json_data = return_obj.get('json')
                error_list = return_obj.get('error_list')
                if error_list:
                    messages.error(request, error_list)
                    return redirect(reverse("dashboard"))
                return_obj = json_to_import(json_data, Inventory.objects.create(name=name))
                inventory = return_obj.get('inventory')
                error_list = return_obj.get('error_list')
                if not error_list:
                    messages.success(request, "L'import est un succés. L'inventaire est mis a jour.")
                else:
                    messages.error(request, f'Error while extracting : {error_list}')
                return redirect(reverse("inventory", args=[inventory.id, 0]))
            else:
                messages.error(request, f'Les fichiers de type {file_extension} ne sont pas pris en charge.')
        #except Exception as e:
        #    logger.error(f'{e} - {request}')
        #    messages.error(request, f'error while saving {e}')
    return redirect(reverse("dashboard"))


@login_required
def export_inventory(id=None, *args, **kwargs):
    inventory = Inventory.objects.get(id=id)
    backup = save_backup(inventory)
    df = pd.DataFrame.from_dict(
        [p.as_Kesia2_inventory_dict() for p in inventory.products.all()],
        orient='columns'
        )
    file_path = f'{settings.MEDIA_ROOT}/{inventory.name}_{str(backup.date_creation)[:10]}.xlsx'
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

@login_required
def delete_inventory(request, id=None, *args, **kwargs):
    inventory = Inventory.objects.get(id=id)
    # watchout #
    for product in inventory.products.all():
        logger.info(inventory.products.len())
        product.delete()
    inventory.delete()
    messages.success(request, "Your inventory has been deleted.")
    return redirect(reverse("dashboard"))

def save_backup(inventory, type=Backup.BackupType.AUTO):
    backup = Backup(
        inventory=inventory,
        products_backup = pd.DataFrame([x.as_Kesia2_dict() for x in inventory.products.all()]).to_json(orient='table'),
        transactions_backup = pd.DataFrame([x.as_dict() for x in inventory.transactions.all()]).to_json(orient='table'),
        backup_type = type
    )
    backup.save()
    return(backup)
