from itertools import chain
from django.shortcuts import redirect, render
from django.conf import settings
import os

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import Http404, HttpResponse


import pandas as pd
from inventory.models import Receipt, Transaction
from inventory.views import save_backup
from .models import Delivery, delivery_columns
from home.views import init_context
from django.contrib import messages

@login_required
def delivery_list_view(request, *args, **kwargs):
    context = init_context()

    query = request.GET.get('search', '')  # Récupère le texte de recherche
    delivery_list = context['delivery_list']
    # Filtre les produits si une recherche est spécifiée
    if query:
        delivery_list = delivery_list.filter(provider__name=query)
    total = len(delivery_list)
    
    paginator = Paginator(delivery_list, 25)  # 25 produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)  
    pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*25    

    context['columns'] = delivery_columns
    context['delivery_list'] = page_obj.object_list
    context["pages"] = page_obj
    context["total"] = total
    context["len"] = pagin
    return render(request, "delivery/delivery_list/delivery.html", context)

@login_required
def delivery_view(request, id=None, *args, **kwargs):
    context = init_context()
    delivery = Delivery.objects.last()
    inventory = delivery.inventory
    transactions = delivery.transactions.all()
    iproducts = []

    total = transactions.count()

    for transaction in transactions:
        if transaction.iproduct.product.has_changed:
            messages.warning(request, f'Le prix de {transaction.iproduct.product.description} a changé !')
        elif transaction.iproduct.product.multicode_generated:
            messages.warning(request, f'Le multicode de {transaction.iproduct.product.description} a été généré !')
        iproducts.append(transaction.iproduct)

    paginator = Paginator(iproducts, 25)  # 25 produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*25


    context["delivery"] = delivery
    context["inventory"] = inventory
    context["columns"] = settings.INVENTORY_COLUMNS_NAME.values()
    context["iproducts"] = page_obj.object_list
    context["pages"] = page_obj
    context["total"] = total
    context["len"] = pagin

    return render(request, "delivery/delivery.html", context)

@login_required
def update_transaction(request, delivery=None, id=None, *args, **kwargs):
    if request.method == 'POST':
        transaction = Transaction.objects.get(id=id)
        transaction.quantity = request.POST.get('quantity', transaction.quantity)
        
        transaction.save()
    return redirect(reverse("delivery", args=[delivery]))

@login_required
def validate_delivery(request, id=None, *args, **kwargs):
    try:
        delivery = Delivery.objects.get(id=id)
        receipt, created = Receipt.objects.get_or_create(is_waiting=True)
        for transaction in delivery.transactions.all():
            receipt.iproducts.add(transaction.iproduct)
        receipt.save()
        delivery.is_validated = True
        delivery.save()
        messages.success(request, f'Livraison validée et ajoutée aux réceptions.')
    except Exception as e:
        messages.error(request, f'Error while validate {e}')
    return redirect(reverse("receipt"))

@login_required
def export_delivery(request, id=None, *args, **kwargs):
    delivery = Delivery.objects.get(id=id)
    df = pd.DataFrame.from_dict(
        [t.iproduct.as_dict() for t in delivery.transactions.all()],
        orient='columns'
        )
    file_path = f'{settings.MEDIA_ROOT}/delivery{delivery.id}_{str(delivery.date_creation)[:10]}.xlsx'
    df.to_excel(file_path, index=False)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def delete_delivery(request, id=None, *args, **kwargs):
    delivery = Delivery.objects.get(id=id)
    delivery.delete()
    messages.success(request, f'la livraison a bien été supprimé. ')
    return redirect(reverse("delivery_list"))

@login_required
def receipt_view(request, *args, **kwargs):
    context = init_context()

    query = request.GET.get('search', '')  # Récupère le texte de recherche
    iproducts = context["receipt"].iproducts.all()
    # Filtre les produits si une recherche est spécifiée
    if query:
        iproducts_desc = iproducts.filter(product__description__icontains=query)
        iproducts_prov = iproducts.filter(product__provider__name=query)
        iproducts = list(chain(iproducts_desc, iproducts_prov))
        total = len(iproducts)
    else:
        total = iproducts.count()

    paginator = Paginator(iproducts, 25)  # 25 produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*25

    context["columns"] = settings.INVENTORY_COLUMNS_NAME.values()
    context["iproducts"] = page_obj.object_list
    context["pages"] = page_obj
    context["total"] = total
    context["len"] = pagin
    return render(request, "inventory/receipt.html", context)
    

@login_required
def export_receipt(*args, **kwargs):
    receipt = Receipt.objects.first()
    backup = save_backup(receipt)
    df = pd.DataFrame.from_dict(
        [p.as_receipt() for p in receipt.iproducts.all()],
        orient='columns'
        )
    file_path = f'{settings.MEDIA_ROOT}/{receipt.name}_{str(backup.date_creation)[:10]}.xlsx'
    df.to_excel(file_path, index=False)
    receipt.is_waiting=False
    receipt.save()
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def empty_receipt(request, *args, **kwargs):
    receipt = Receipt.objects.first()
    for p in receipt.iproducts.all():
        p.delete()
    receipt.is_waiting=True
    receipt.save()
    messages.success(request, 'Reception mis a jour.')
    return redirect(reverse("receipt")) 

#@login_required
#def update_delivery_product(request, delivery=None, product=None, *args, **kwargs):
#    if request.method == 'POST':
#        product = Product.objects.get(id=product)
#        form = ProductForm(request.POST)
#        product.description = form.data['description']
#        product.quantity = form.data['quantity']
#        product.save()
#    return redirect(reverse("inventory", args=[inventory, 0]))
