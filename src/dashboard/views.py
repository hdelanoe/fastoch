from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse

from inventory.models import Inventory
from home.views import init_context

@login_required
def dashboard_view(request):
    context = init_context()
    return render(request, "dashboard/dashboard.html", context) 

@login_required
def create_inventory(request):
    if request.method=='POST':
        try:
            Inventory.objects.create(name=request.POST.get('name', "My inventory"))
            messages.success(request, "Your inventory has been created.")
        except Inventory.DoesNotExist:
            messages.error(request, "Error while create your inventory.")
    return redirect(reverse("dashboard"))
