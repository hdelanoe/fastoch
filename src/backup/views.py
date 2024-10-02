from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Backup, backup_columns
from inventory.models import Inventory

@login_required
def backup_view(request, *args, **kwargs):
    inventory_list = Inventory.objects.all()
    backup_list = Backup.objects.all()
    context = {
        "backup_list": backup_list,
        "inventory_list": inventory_list,
        "columns": backup_columns,
    }
    return render(request, "backup/backup.html", context) 
