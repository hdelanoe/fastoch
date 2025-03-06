import pathlib
from django.shortcuts import redirect

from inventory.models import Inventory
from provider.models import Provider

from backup.models import Backup


this_dir = pathlib.Path(__file__).resolve().parent

def home_view(request, *args, **kwargs):
    return redirect("dashboard")

def init_context():
    try:
        inventory_list = Inventory.objects.all().order_by('is_current')
    except:
        inventory_list = None
    try:
        provider_list = Provider.objects.all().order_by('name')
    except:
        provider_list = None
    try:
        backup_list = Backup.objects.all()
    except Backup.DoesNotExist:
        backup_list = None    
    return {
        "inventory_list": inventory_list,
        "provider_list": provider_list,
        "backup_list": backup_list,
    }
