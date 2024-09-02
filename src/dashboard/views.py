from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from customers.models import Customer
from inventory.models import Inventory

@login_required
def dashboard_view(request):
    customer = Customer.get_customer_by_user_email(request.user.email)
    inventory_obj = Inventory.objects.get_or_create(customer=customer)[0]
    print(inventory_obj.customer)
    print(inventory_obj.products.all())
    context = {
        "entry_list": inventory_obj.products.all()
    }
    return render(request, "dashboard/dashboard.html", context) 