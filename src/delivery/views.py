from django.shortcuts import render
from django.conf import settings
import os

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse


import pandas as pd
from inventory.models import Inventory
from .models import Delivery, delivery_columns
from dashboard.views import init_context

@login_required
def delivery_view(request, *args, **kwargs):
    context = init_context()
    context['columns'] = delivery_columns
    return render(request, "delivery/delivery_list/delivery.html", context) 

@login_required
def last_delivery_view(request, inv_id=None, id=None, *args, **kwargs):
    context = init_context()
    delivery = Delivery.objects.get(id=id)
    inventory = Inventory.objects.get(id=inv_id)
    context["delivery"] = delivery
    context["inventory"] = inventory
    context["columns"] = settings.KESIA_COLUMS_NAMES.values()
    context["products"] = delivery.products.all()
    return render(request, "delivery/delivery.html", context)

@login_required
def export_delivery(request, id=None, *args, **kwargs):

    delivery = Delivery.objects.get(id=id)
    columns = Kesia2_column_names.values()
    df = pd.DataFrame([p.as_Kesia2_dict() for p in delivery.products.all()], columns = columns,)
    file_path = f'{settings.MEDIA_ROOT}/{delivery.inventory_name}_{str(delivery.date_creation)[:10]}.xlsx'
    df.to_excel(file_path, index=False)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404
