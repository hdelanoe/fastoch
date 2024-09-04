from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse

from customers.models import Customer
from inventory.models import Inventory
from .forms import NameForm

@login_required
def dashboard_view(request):
    customer = Customer.get_customer_by_user_email(request.user.email)
    try:
        inventory_obj = Inventory.objects.get(customer=customer)
        inventory_list = [inventory_obj]
    except Inventory.DoesNotExist:
        inventory_obj = None
        inventory_list = None
    context = {
        "inventory_list": inventory_list,
    }
    return render(request, "dashboard/dashboard.html", context) 


def create_inventory(request):
    if request.method=='POST':
        form = NameForm(request.POST)
        print(form.data)
        try:
            customer = Customer.get_customer_by_user_email(request.user.email)
            Inventory.objects.create(customer=customer, name=form.data['name'])
            messages.success(request, "Your inventory has been created.")
        except Inventory.DoesNotExist:
            messages.error(request, "Error while create your inventory.")
    return redirect(reverse("dashboard"))