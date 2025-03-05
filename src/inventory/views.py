import re
import os
import logging
import json

import pandas as pd
from itertools import chain

from django.conf import settings
from django.http import Http404,HttpResponseBadRequest, HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from helpers.mistral import Codestral_Mamba
from .forms import ImportForm, EntryForm, QuestionForm
from .parsers import file_to_json, json_to_delivery, json_to_import, validate_ean
from inventory.models import DLC, Inventory, Product, iProduct, Provider
from backup.models import Backup
from settings.models import Settings

from django.db.models import Min, ExpressionWrapper, DurationField
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear
from django.utils import timezone

from home.views import init_context

logger = logging.getLogger('fastoch')

@login_required
def inventory_view(request, name=None, query=None, *args, **kwargs):
    today = timezone.now().date()
    context = init_context()
    try:
        inventory = Inventory.objects.get(name=name)
    except Inventory.DoesNotExist:
        messages.error(request, f"Aucun inventaire trouvé avec le nom '{name}'.")
        return redirect(reverse("dashboard"))
    iproducts = inventory.iproducts.annotate(
        closest_date=Min('dates__date')
    ).annotate(
        date_diff=ExpressionWrapper(
            (ExtractYear('closest_date') - ExtractYear(today)) * 365 +
            (ExtractMonth('closest_date') - ExtractMonth(today)) * 30 +
            (ExtractDay('closest_date') - ExtractDay(today)),
            output_field=DurationField()
        )
    ).order_by('date_diff')

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
    context["iproducts"] = page_obj.object_list
    context["pages"] = page_obj
    context["total"] = total
    context["len"] = pagin
    
    context["inventory"] = inventory
    request.session["context"] = "inventory"
    request.session["query"] = query
    context["temp"] =False

    return render(request, "inventory/inventory.html", context)

@login_required
def move_iproducts(request, id):
    if request.method == 'POST':
        source_inventory = get_object_or_404(Inventory, id=id)
        target_inventory = get_object_or_404(Inventory, id=request.POST.get('target_inventory'))

        # Déplacer tous les iproducts vers l'inventaire cible
        iproducts_to_move = source_inventory.iproducts.all()
        for iproduct in iproducts_to_move:
            iproduct.inventory = target_inventory
            iproduct.save()

        # Rediriger vers la page de l'inventaire cible après le déplacement
        return redirect('inventory', name=target_inventory.name)


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
        logger.debug(f' REQUEST : {request.POST}')
        form = EntryForm(request.POST)

        try:
            iproduct_obj = iProduct.objects.get(id=iproduct)
            logger.debug(f'iproduct = {iproduct_obj}')

        except iProduct.DoesNotExist:
            iproduct_obj = None

        product_obj = Product.objects.get(id=product)
        provider = product_obj.provider
        ean = request.POST.get('ean', product_obj.ean)

        #if validate_ean(ean) is True:
        #    logger.debug('ean valid')
        #else :
        #    logger.debug(f'EAN non valide.')
        #    raise HttpResponseBadRequest
        if validate_ean(ean) is True and str(ean) != str(product_obj.ean):
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

        if provider.erase_multicode is True and validate_ean(product_to_update.ean) is True:
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
def import_inventory_json(request):
    if request.method == 'POST' and request.FILES['json_file']:
        # Charger le fichier JSON depuis le formulaire
        json_file = request.FILES['json_file']
        try:
            data = json.load(json_file)  # Charger le fichier JSON
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON file"}, status=400)
        
        # Créer ou récupérer l'inventaire
        inventory, created = Inventory.objects.get_or_create(name="Imported Inventory")
        
        # Traitement des données
        for item in data:
            try:
                # Créer ou récupérer le produit
                product, created = Product.objects.get_or_create(
                    ean=item['EAN'],
                    multicode=item['Code'],
                    defaults={
                        'description': item['DEF'],
                        'achat_ht': item['PMPA'],
                        'is_new': True,
                        'has_changed': False
                    }
                )
                # Créer l'iProduct
                iproduct, created = iProduct.objects.get_or_create(
                    inventory=inventory,
                    product=product,
                    defaults={'quantity': item['STOCK']}
                )
                if 'DLC' in item:
                    dlc_date = item['DLC']
                    if isinstance(dlc_date, str):
                        
                        # Vérifier que DLC est une chaîne de caractères
                        try:
                            # Essayer de convertir la date en format YYYY-MM-DD
                            dlc_date_parsed = timezone.datetime.strptime(dlc_date, "%Y-%m-%d").date()
                            
                            # Créer ou récupérer la DLC
                            DLC.objects.get_or_create(iproduct=iproduct, date=dlc_date_parsed)
                        except ValueError:
                            return JsonResponse({"error": f"Invalid date format for DLC: {dlc_date}"}, status=400)
                    else:
                        return JsonResponse({"error": f"Invalid type for DLC: {dlc_date}, expected a string representing a date."}, status=400)

            except KeyError as e:
                return JsonResponse({"error": f"Missing key {str(e)} in the JSON data"}, status=400)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "A referenced object does not exist"}, status=400)

        return redirect(reverse("inventory", args=[inventory.name]))

    return render(request, 'dashboard.html')

@login_required
def import_inventory(request, *args, **kwargs):
    logger.debug(f'REQUEST : {request}')
    if request.method == 'POST':
        try:
            name = request.POST['name']
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
            else :
                try:
                    inventories=Inventory.objects.all()
                    if not inventories:
                        Inventory.objects.create(
                            name=name,
                            is_current=True, is_waiting=False)
                    else:
                        Inventory.objects.create(name=name)    
                    messages.success(request, "Your inventory has been created.")
                    return redirect(reverse("inventory", args=[name]))    
                except Inventory.DoesNotExist:
                    messages.error(request, "Error while create your inventory.")
                    return redirect(reverse("dashboard"))
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
                #messages.warning(return_obj['report'])
                return redirect(reverse("inventory", args=[name]))
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
    iproducts= inventory.iproducts.all()
    backup = save_backup(inventory)
    df = pd.DataFrame.from_dict(
        [p.as_dict() for p in iproducts],
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

def export_inventory_json(request, id):
    try:
        inventory = Inventory.objects.get(id=id)
        data = []

        for iproduct in inventory.iproducts.all():
            product_data = iproduct.as_dict()  # Récupérer les infos de l'iProduct
            
            # Ajouter la DLC la plus proche (future ou passée)
            closest_dlc = iproduct.get_closest_dlc()
            if closest_dlc:
                product_data['DLC'] = str(closest_dlc)  # Ajouter la date de la DLC
            else:
                product_data['DLC'] = None  # Aucune DLC disponible

            data.append(product_data)

        return JsonResponse(data, safe=False, json_dumps_params={'indent': 4, 'ensure_ascii': False})

    except Inventory.DoesNotExist:
        return JsonResponse({"error": "Inventory not found"}, status=404)

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
    for iproduct in inventory.iproducts.all():
        logger.info(inventory.iproducts.all().count())
        iproduct.delete()
    inventory.delete()
    messages.success(request, "Your inventory has been deleted.")
    return redirect(reverse("dashboard"))

def save_backup(inventory, type=Backup.BackupType.AUTO):
    iproducts=inventory.iproducts.all()
    backup = Backup(
        inventory=inventory,
        iproducts_backup = pd.DataFrame([x.as_dict() for x in iproducts]).to_json(orient='table'),
        #transactions_backup = pd.DataFrame([x.as_Kesia2_inventory_dict() for x in inventory.transactions.all()]).to_json(orient='table'),
        backup_type = type
    )
    backup.save()
    return(backup)
