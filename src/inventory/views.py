import re
import os
import logging

import pandas as pd
from itertools import chain

from django.conf import settings
from django.http import Http404,HttpResponseBadRequest, HttpResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from helpers.mistral import Codestral_Mamba
from .forms import ImportForm, EntryForm, QuestionForm
from .parsers import file_to_json, json_to_delivery, json_to_import, validate_ean
from inventory.models import Inventory, Product, iProduct, Provider
from backup.models import Backup
from settings.models import Settings
from delivery.views import receipt_view

from home.views import init_context

logger = logging.getLogger('fastoch')


@login_required
def inventory_view(request, response=0, query=None, *args, **kwargs):
    context = init_context()
    iproducts = iProduct.objects.filter(container_name=context["inventory"].name)
    
    if not query:
        query = request.GET.get('search', '')  # Récupère le texte de recherche
    # Filtre les produits si une recherche est spécifiée
    if query:
        iproducts_desc = iproducts.filter(product__description__icontains=query)
        iproducts_prov = iproducts.filter(product__provider__name=query)
        iproducts_code = iproducts.filter(product__multicode__icontains=query)
        iproducts = list(chain(iproducts_desc, iproducts_prov, iproducts_code))
        total = len(iproducts)
    else:
        total = iproducts.count()

    settings_value, created = Settings.objects.get_or_create(id=1)

    paginator = Paginator(iproducts, settings_value.pagin)  # settings_value.pagin produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*settings_value.pagin

    context["columns"] = settings.INVENTORY_COLUMNS_NAME.values()
    context["response"] = response
    context["iproducts"] = page_obj.object_list
    context["pages"] = page_obj
    context["total"] = total
    context["len"] = pagin

    request.session["context"] = "inventory"
    request.session["query"] = query
    context["temp"] =False

    return render(request, "inventory/inventory.html", context)

@login_required
def move_from_file(request, *args, **kwargs):
    inventory = Inventory.objects.get(is_current=True)
    if request.method == 'POST':
        try:
            form = ImportForm(request.POST)
            uploaded_file = request.FILES['document']
            providername = form.data['provider']
            move_type = int(form.data['move_type'])
            filename, file_extension = os.path.splitext(uploaded_file.name)
            if file_extension == ".pdf" or file_extension == ".png" or file_extension==".heic" or file_extension == ".xml" or file_extension == ".xlsx" or file_extension == ".xls" or file_extension == ".csv":
                # Parsing file #
                return_obj = file_to_json(uploaded_file, file_extension)
                json_data = return_obj.get('json')
                error_list = return_obj.get('error_list')
                if error_list:
                    messages.error(request, error_list)
                    return redirect(reverse("inventory", args=[0]))
                # Parsing json #
                return_obj = json_to_delivery(providername, json_data, move_type)
                error_list = return_obj.get('error_list')
                delivery = return_obj.get('delivery')
                if error_list:
                    messages.error(request, f'Error while extracting : {error_list}')
                else:
                    messages.success(request, "Livraison bien enregistrée.")
                return redirect(reverse('delivery', args=[delivery.id]))
            else:
                messages.error(request, f'Les fichiers de type {file_extension} ne sont pas pris en charge.')
        except Exception as e:
            messages.error(request, f'error while saving {e}')
    if str(request.session['context']) == "delivery":
        return redirect(reverse("delivery", args=[request.session['contextid']]))        
    return redirect(reverse("inventory", args=[0]))




@login_required
def update_product(request, iproduct=None, product=None, *args, **kwargs):
    if request.method == 'POST':
        logger.debug(f'{request.POST.get('achat_brut', None)}')        
        logger.debug(f' REQUEST : {request.POST}')
        settings, created = Settings.objects.get_or_create(id=1)  
        if created:
            settings.erase_multicode=False      
        form = EntryForm(request.POST)
        try:
            iproduct_obj = iProduct.objects.get(id=iproduct)
            logger.debug(f'iproduct = {iproduct_obj}')
        except iProduct.DoesNotExist:
            iproduct_obj = None      
        product_obj = Product.objects.get(id=product)
        ean = request.POST.get('ean', product_obj.ean)
        if validate_ean(ean) is True:
            logger.debug('ean valid')
        else:
            logger.debug(f'EAN non valide.')
            raise HttpResponseBadRequest        
        if validate_ean(ean) is True and ean != product_obj.ean:
            try:
                logger.debug(f'new ean : {ean} -> {product_obj.ean}')
                replace_product = Product.objects.get(ean=ean)
                messages.warning(request, f'{product_obj.description} a ete remplace par {replace_product.description} lors du changement d\'EAN')
                replace_product.is_new=False
                if replace_product.achat_ht != product_obj.achat_ht:
                    replace_product.achat_ht = product_obj.achat_ht
                    replace_product.has_changed = True
                product_obj.delete()
                product_to_update = replace_product
            except (Product.DoesNotExist, Product.MultipleObjectsReturned) :
                product_to_update = product_obj
                product_to_update.ean = ean
                
                product_to_update.description = request.POST.get('description', product_to_update.description)

        else:
            product_to_update = product_obj
            if validate_ean(ean) is True:
                product_to_update.ean = ean
            product_to_update.description = request.POST.get('description', product_to_update.description)
            logger.debug('update desc')

        if settings.erase_multicode is True and validate_ean(product_to_update.ean) is True:
            try:
                same_multicode=Product.objects.get(multicode=product_to_update.ean)
                logger.error(f'product {same_multicode.description} a le meme multicode -> {product_to_update.ean}')
            except Product.DoesNotExist:    
                product_to_update.multicode = product_to_update.ean
                product_to_update.multicode_generated = False
        else:
            if product_to_update.multicode != request.POST.get('multicode', product_to_update.multicode):        
                product_to_update.multicode = request.POST.get('multicode', product_to_update.multicode)
                product_to_update.multicode_generated = False

        try:
            providername = form.data['providername']
            provider, created = Provider.objects.get_or_create(name = providername)
            product_to_update.provider = provider
        except Exception:
            None


        product_to_update.achat_ht = re.search(
                    r'([0-9]+.?[0-9]+)', str(request.POST.get('achat_ht', product_to_update.achat_ht)).replace(',', '.')
                    ).group(1)
        product_to_update.has_changed=False
        try:
            product_to_update.save()
        except Exception as e:
            logger.error(f'Erreur pendant la mis a jour du produit : {e}')
            raise Http404

        if iproduct_obj:
            iproduct_obj.product = product_to_update
            iproduct_obj.quantity = request.POST.get('quantity', iproduct_obj.quantity)
            iproduct_obj.save()
        return HttpResponse("sucess")    
    raise Http404

#@login_required
#def delete_product(request, product=None, *args, **kwargs):
#    if request.method == 'POST':
#        product_obj = Product.objects.get(id=product)
#        product_obj.delete()
#    if str(request.session['context']) == "delivery":
#        return redirect(reverse("delivery", args=[request.session['contextid']]))    
#    return redirect(reverse("inventory", args=[0]))

@login_required
def delete_iproduct(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        iproduct = iProduct.objects.get(id=id)
        iproduct.delete()
        messages.success(request, f'Produit supprimé.')
    if str(request.session['context']) == "delivery":
        return redirect(reverse("delivery", args=[request.session['contextid']]))
    elif str(request.session['context']) == "receipt":    
         return redirect(reverse("receipt"))
    return redirect(reverse("inventory", args=[0]))

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
    return redirect(reverse("inventory", args=[1]))


@login_required
def import_inventory(request, *args, **kwargs):
    if request.method == 'POST':
        try:
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
                return_obj = json_to_import(json_data, Inventory.objects.create(name=name, is_current=True))
                inventory = return_obj.get('inventory')
                error_list = return_obj.get('error_list')
                if not error_list:
                    for inv in Inventory.objects.all():
                        if inv is not inventory:
                            inv.is_current=False
                    messages.success(request, "L'import est un succés. L'inventaire est mis a jour.")
                else:
                    for error in error_list:
                        logger.error(error)
                        messages.error(request, error)
                messages.warning(return_obj['report'])        
                return redirect(reverse("inventory", args=[0]))
            else:
                messages.error(request, f'Les fichiers de type {file_extension} ne sont pas pris en charge.')
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.error(f'{message}')
            messages.error(request, f'Erreur lors de la sauvegarde du fichier : {ex}')
    return redirect(reverse("dashboard"))


@login_required
def export_inventory(request, id=None, *args, **kwargs):
    inventory = Inventory.objects.get(is_current=True)
    iproducts=iProduct.objects.filter(container_name=inventory.name)
    backup = save_backup(inventory)
    df = pd.DataFrame.from_dict(
        [p.as_receipt() for p in iproducts],
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
    messages.success(request, "Your inventory has been saved.")
    return redirect(reverse("inventory", args=[0]))

@login_required
def delete_inventory(request, id=None, *args, **kwargs):
    inventory = Inventory.objects.get(id=id)
    # watchout #
    for product in inventory.products.all():
        logger.info(inventory.products.all().count())
        product.delete()
    inventory.delete()
    messages.success(request, "Your inventory has been deleted.")
    return redirect(reverse("dashboard"))

def save_backup(inventory, type=Backup.BackupType.AUTO):
    iproducts=iProduct.objects.filter(container_name=inventory.name)
    backup = Backup(
        inventory=inventory,
        iproducts_backup = pd.DataFrame([x.as_dict() for x in iproducts]).to_json(orient='table'),
        #transactions_backup = pd.DataFrame([x.as_Kesia2_inventory_dict() for x in inventory.transactions.all()]).to_json(orient='table'),
        backup_type = type
    )
    backup.save()
    return(backup)
