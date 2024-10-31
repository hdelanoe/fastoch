from django.db import models

from inventory.models import TransactionList

delivery_columns = ['from_inventory', 'creation_date']

class Delivery(TransactionList):
    inventory_name = models.CharField(max_length=50, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
