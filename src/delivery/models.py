from django.db import models

from inventory.models import ProductList

delivery_columns = ['from_inventory', 'creation_date']

class Delivery(ProductList):
    inventory_name = models.CharField(max_length=50, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
