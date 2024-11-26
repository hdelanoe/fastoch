import pathlib
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages

from inventory.models import Inventory
from backup.models import Backup
from provider.models import Provider
from delivery.models import Delivery

this_dir = pathlib.Path(__file__).resolve().parent

def home_view(request, *args, **kwargs):
    return redirect("dashboard")

def init_context():
    try:
        inventory_list = Inventory.objects.all()
    except Inventory.DoesNotExist:
        inventory_list = None
    try:
        provider_list = Provider.objects.all()
    except Provider.DoesNotExist:
        provider_list = None
    try:
        backup_list = Backup.objects.all()
    except Backup.DoesNotExist:
        backup_list = None    
    try:
        delivery_list = Delivery.objects.all()[::-1]
    except Delivery.DoesNotExist:
        delivery_list = None        
    return {
        "inventory_list": inventory_list,
        "backup_list": backup_list,
        "provider_list": provider_list,
        "delivery_list": delivery_list,
    }
