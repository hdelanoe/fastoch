from itertools import chain
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from django.conf import settings

import json
import pandas as pd

from .models import Backup, backup_columns
from inventory.models import Product, Provider
from inventory.views import save_backup
from home.views import init_context


@login_required
def backup_view(request, *args, **kwargs):
    context = init_context()

    query = request.GET.get('search', '')  # Récupère le texte de recherche
    backup_list = Backup.objects.all()
    # Filtre les produits si une recherche est spécifiée
    if query:
        backup_type_list = backup_list.filter(backup_type__icontains=query)
        backup_inv_list = backup_list.filter(inventory__name=query)
        backup_list = list(chain(backup_type_list, backup_inv_list))
        total = len(backup_list)
    else:
        total = backup_list.count()

    paginator = Paginator(backup_list, 25)  # 25 produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*25

    context['columns'] = backup_columns
    context["pages"] = page_obj
    context["backup_list"] = page_obj.object_list
    context["total"] = total
    context["len"] = pagin
    return render(request, "backup/backup.html", context)

@login_required
def delete_backup(request, id=None, *args, **kwargs):
    try:
        backup = Backup.objects.get(id=id)
        backup.delete()
        messages.success(request, f'Le backup a bien été supprimé.')
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression du backup : {e}')

    return redirect(reverse("backup"))

@login_required
def restore_backup(request, id=None, *args, **kwargs):
    messages.warning(request, f'Fonctionnalité en développement.')
    return redirect(reverse("backup"))
    backup = Backup.objects.get(id=id)
    inventory = backup.inventory
    products_data = json.loads(backup.products_backup)['data']
    save_backup(inventory)
    try:
        for p in inventory.products.all():
            p.delete()
        for t in inventory.transactions.all():
            t.delete()
        inventory.save()
        for p in products_data:
            code_art=p[settings.KESIA2_COLUMNS_NAME['code_art']]
            provider, created = Provider.objects.get_or_create(
                        name=p[settings.KESIA2_COLUMNS_NAME['provider']],
                        code=str(p[settings.KESIA2_COLUMNS_NAME['provider']]).replace(' ', '')[:3].upper())
            ean=p[settings.KESIA2_COLUMNS_NAME['ean']]
            description=p[settings.KESIA2_COLUMNS_NAME['description']]
            quantity=p[settings.KESIA2_COLUMNS_NAME['quantity']]
            achat_ht=p[settings.KESIA2_COLUMNS_NAME['achat_ht']]
            vente_net=p[settings.KESIA2_COLUMNS_NAME['vente_net']]
            try:
                if ean.isdigit():
                    product = Product.objects.get(ean=ean)
                else:
                    raise Product.DoesNotExist('EAN is not a digit')
            except Product.DoesNotExist:
                try:
                    if code_art is not None:
                        product = Product.objects.get(code_art=code_art)
                    else:
                        raise Product.DoesNotExist('No code article')
                except Product.DoesNotExist:
                    product = Product.objects.create(
                        provider=provider,
                        description=description)
                    if code_art is None:
                        code_art = f'{provider.code}{product.id}'
                    product.multicode = code_art
                    if ean.isdigit():
                        product.ean = ean
            inventory.append(product)
        #for t in transactions_data:
        #    inventory.add(t)
        inventory.save()
        messages.success(request, f'Le backup a été restaurer.')
        return redirect(reverse("inventory", args=[0]))
    except Exception as e:
        messages.error(request, f'Erreur lors de la restauration du backup : {e}')
    return redirect(reverse("backup"))
