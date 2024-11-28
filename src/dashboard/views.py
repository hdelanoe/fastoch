from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse

from inventory.models import Inventory
from home.views import init_context

@login_required
def dashboard_view(request):
    context = init_context()
    if not context["inventory_list"] :
        return render(request, "dashboard/dashboard_new_inventory.html", context)
    inventory = Inventory.objects.get(is_current=True)
    context["inventory"] = inventory
    return render(request, "dashboard/dashboard.html", context) 

@login_required
def create_inventory(request):
    if request.method=='POST':
        try:
            inventories=Inventory.objects.all()
            if not inventories:
                Inventory.objects.create(
                    name=request.POST.get('name', "My inventory"),
                    is_current=True)
            else:    
                Inventory.objects.create(name=request.POST.get('name', "My inventory"))
            messages.success(request, "Your inventory has been created.")
        except Inventory.DoesNotExist:
            messages.error(request, "Error while create your inventory.")
    return redirect(reverse("dashboard"))

@login_required
def add_product_from_photo(request):
    messages.warning(request, "Feature en dev.")
    return redirect(reverse("dashboard"))
