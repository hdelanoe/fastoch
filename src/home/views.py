import pathlib
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse

from inventory.models import Inventory
from backup.models import Backup
from provider.models import Provider
from delivery.models import Delivery

this_dir = pathlib.Path(__file__).resolve().parent

def home_view(request, *args, **kwargs):
    return redirect("dashboard")

@login_required
def dashboard_view(request):
    context = init_context()
    return render(request, "overview/overview.html", context) 


def create_inventory(request):
    if request.method=='POST':
        try:
            Inventory.objects.create(name=request.POST.get('name', "My inventory"))
            messages.success(request, "Your inventory has been created.")
        except Inventory.DoesNotExist:
            messages.error(request, "Error while create your inventory.")
    return redirect(reverse("dashboard"))


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
