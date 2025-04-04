from itertools import chain
import logging
from django.shortcuts import redirect, render
from django.conf import settings
import os
import re

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import Http404, HttpResponse


import pandas as pd
from inventory.models import Inventory, Product, iProduct
from .models import Delivery, delivery_columns
from .forms import AddiProductForm
from home.views import init_context
from django.contrib import messages

from django.db.models import Min, ExpressionWrapper, DurationField
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear
from django.utils import timezone

logger = logging.getLogger('fastoch')

@login_required
def delivery_list_view(request, query=None, *args, **kwargs):
    context = init_context()
    delivery_list = context['delivery_list']

    if not query:
        query = request.GET.get('search', '')

    if query:
        delivery_list = delivery_list.filter(provider__name=query)
        total = len(delivery_list)
    else:
        total = delivery_list.count()

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
    try:
        delivery = Delivery.objects.get(id=id)
    except Delivery.DoesNotExist:
        messages.error(request, 'Erreur lors de l\'affichage de la livraison')
        return render(request, "delivery/delivery_list/delivery.html", context)
    iproducts = iProduct.objects.filter(container_name=str(delivery.date_time))

    total = iproducts.count()

    for iproduct in iproducts:
        if iproduct.product.has_changed:
            messages.warning(request, f'Le prix de {iproduct.product.description} a changé !')
        elif iproduct.product.multicode_generated:
            messages.warning(request, f'Le multicode de {iproduct.product.description} a été généré !')

    paginator = Paginator(iproducts, 25)  # 25 produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*25


    # Disable paginator
    #paginator = Paginator(iproducts, 25)  # 25 produits par page
    #page_number = request.GET.get('page')
    #page_obj = paginator.get_page(page_number)
    #pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*25

    #context["pages"] = page_obj
    #context["len"] = pagin
    context["total"] = total


    context["iproducts"] = iproducts
    context["delivery"] = delivery
    context["columns"] = settings.DELIVERY_COLUMNS_NAME.values()

    request.session["context"] = "delivery"
    request.session["contextid"] = delivery.id
    context["temp"] = True

    return render(request, "delivery/delivery.html", context)


@login_required
def validate_delivery(request, id=None, *args, **kwargs):
    try:
        delivery = Delivery.objects.get(id=id)
        reception, created = Inventory.objects.get_or_create(name='reception')
        logger.debug(f'{str(delivery.date_time)}')
        iproducts = iProduct.objects.filter(container_name=str(delivery.date_time))
        df = pd.DataFrame.from_dict(
            [p.as_dict() for p in iproducts],
            orient='columns'
            )
        file_path = f'{settings.MEDIA_ROOT}/delivery{delivery.id}_{str(delivery.date_time)[:10]}.xlsx'
        df.to_excel(file_path, index=False)
        if reception.is_waiting:
            for iproduct in iproducts:
                try:
                    already = iProduct.objects.get(product=iproduct.product,
                                                container_name=reception.name)
                    already.quantity += iproduct.quantity
                    already.save()
                    iproduct.delete()
                except:
                    iproduct.container_name=reception.name
                    iproduct.save()
            reception.save()
            delivery.is_validated = True
            delivery.save()
            messages.success(request, f'Livraison validée et ajoutée aux réceptions.')
        else:
            messages.error(request, f'Videz d\'abord la réception')
    except Exception as e:
        messages.error(request, f'Error while validate {e}')
    return redirect(reverse("delivery_list"))


@login_required
def export_delivery(request, id=None, *args, **kwargs):
    delivery = Delivery.objects.get(id=id)
    file_path = f'{settings.MEDIA_ROOT}/delivery{delivery.id}_{str(delivery.date_time)[:10]}.xlsx'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def delete_delivery(request, id=None, *args, **kwargs):
    delivery = Delivery.objects.get(id=id)
    iproducts = iProduct.objects.filter(container_name=str(delivery.date_time))
    for iproduct in iproducts:
        iproduct.delete()
    delivery.delete()
    messages.success(request, f'la livraison a bien été supprimé.')
    return redirect(reverse("delivery_list"))


@login_required
def add_iproduct(request, delivery=None, *args, **kwargs):
    if request.method == 'POST':
        form = AddiProductForm(request.POST)
        delivery = Delivery.objects.get(id=delivery)
        multicode = str(form.data['multicode'])
        ean = int(form.data['ean'])
        description = str(form.data['description'])
        quantity = int(form.data['quantity'])
        achat_ht = float(form.data['achat_ht'])

        try:
            product, created = Product.objects.get_or_create(ean=ean)
            product.multicode = multicode
            product.ean = ean
            product.description = description
            product.achat_ht = float(
            re.search(
                r'([0-9]+.?[0-9]+)', str(achat_ht).replace(',', '.')
                ).group(1)
            )
            product.is_new=False
            product.has_changed=False
            product.multicode_generated=False
            product.save()
            iproduct = iProduct.objects.create(
                container_name = str(delivery.date_time),
                product=product,
                quantity = quantity
            )
            iproduct.save()
            messages.success(request, f'Produit ajouté.')
        except Exception:
           messages.error(request, f'Erreur lors de l\'ajout.')
    if str(request.session['context']) == "delivery":
        return redirect(reverse("delivery", args=[request.session['contextid']]))
    return redirect(reverse("inventory", args=[0]))

#@login_required
#def update_delivery_product(request, delivery=None, product=None, *args, **kwargs):
#    if request.method == 'POST':
#        product = Product.objects.get(id=product)
#        form = ProductForm(request.POST)
#        product.description = form.data['description']
#        product.quantity = form.data['quantity']
#        product.save()
#    return redirect(reverse("inventory", args=[inventory, 0]))
