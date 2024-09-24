from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse

from inventory.models import Inventory
from .forms import NameForm

@login_required
def dashboard_view(request):
    try:
        inventory_list = Inventory.objects.all()
    except Inventory.DoesNotExist:
        inventory_list = None
    context = {
        "inventory_list": inventory_list,
    }
    return render(request, "dashboard/dashboard.html", context) 


def create_inventory(request):
    if request.method=='POST':
        form = NameForm(request.POST)
        try:
            Inventory.objects.create(name=form.data['name'])
            messages.success(request, "Your inventory has been created.")
        except Inventory.DoesNotExist:
            messages.error(request, "Error while create your inventory.")
    return redirect(reverse("dashboard"))