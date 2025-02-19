import pathlib
from django.shortcuts import redirect

from inventory.models import Inventory, Receipt, iProduct
from backup.models import Backup
from provider.models import Provider
from delivery.models import Delivery

this_dir = pathlib.Path(__file__).resolve().parent

def home_view(request, *args, **kwargs):
    return redirect("dashboard")

def init_context():
    try:
        current_inventory = Inventory.objects.get(is_current=True)
    except Inventory.DoesNotExist:
        current_inventory = None
    try:
        provider_list = Provider.objects.all().order_by('name')
    except Provider.DoesNotExist:
        provider_list = None
    try:
        backup_list = Backup.objects.all()
    except Backup.DoesNotExist:
        backup_list = None    
    try:
        delivery_list = Delivery.objects.filter(is_validated=False).order_by('-date_time')
        delivery_has_validate_count = len(delivery_list)
    except Delivery.DoesNotExist:
        delivery_list = None
    try:
        receipt = Receipt.objects.first()
    except Receipt.DoesNotExist:
        receipt = None
    if receipt:
        try:
            waiting_list_count = iProduct.objects.filter(container_name=receipt.name).count()
        except:
            waiting_list_count = None
    else:
        waiting_list_count = None        
    return {
        "backup_list": backup_list,
        "provider_list": provider_list,
        "delivery_list": delivery_list,
        "inventory": current_inventory,
        "receipt": receipt,
        "waiting_list_count": waiting_list_count,
        "delivery_has_validate_count": delivery_has_validate_count,
    }
