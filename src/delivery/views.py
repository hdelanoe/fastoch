from django.shortcuts import redirect, render
from django.conf import settings
import os

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import Http404, HttpResponse


import pandas as pd
from inventory.models import Inventory
from .models import Delivery, delivery_columns
from dashboard.views import init_context
from django.contrib import messages

@login_required
def delivery_view(request, *args, **kwargs):
    context = init_context()
    context['columns'] = delivery_columns
    return render(request, "delivery/delivery_list/delivery.html", context) 

@login_required
def last_delivery_view(request, id=None, *args, **kwargs):
    context = init_context()
    delivery = Delivery.objects.get(id=id)
    inventory = delivery.inventory
    transactions = delivery.transactions.all()
    context["delivery"] = delivery
    context["inventory"] = inventory
    context["columns"] = settings.KESIA2_COLUMNS_NAME.values()
    context["transactions"] = transactions
    message_list=['Attention']
    for transaction in transactions:
        if transaction.product.has_changed:
            message_list.append(f'Le prix de {transaction.product.description} a changé !')
    messages.warning(request, f'error while parsing {message_list}')      
    return render(request, "delivery/delivery.html", context)

@login_required
def validate_delivery(request, id=None, *args, **kwargs):
    try:
        delivery = Delivery.objects.get(id=id)
        inventory = delivery.inventory
        for transaction in delivery.transactions.all():
            product = transaction.product
            product.quantity += transaction.quantity
            product.save()
            inventory.products.add(product)
            inventory.transaction_list.add(transaction)
        inventory.save()
        delivery.is_validated = True
        delivery.save()
        messages.success(request, f'Livraison validé et ajouté a l\'inventaire')    
    except Exception as e:
        messages.error(request, f'Error while validate {e}')    
    return redirect(reverse("last_delivery", args=[delivery.id]))     

@login_required
def export_delivery(request, id=None, *args, **kwargs):
    delivery = Delivery.objects.get(id=id)
    columns = settings.KESIA2_COLUMNS_NAME.values()
    products = []
    for t in delivery.transactions.all():
        products.append(t.product)
    df = pd.DataFrame([p.as_Kesia2_dict() for p in products], columns = columns,)
    file_path = f'{settings.MEDIA_ROOT}/{delivery.inventory.name}_{str(delivery.date_creation)[:10]}.xlsx'
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
    return redirect(reverse("delivery"))  
