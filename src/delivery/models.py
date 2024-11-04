from django.db import models

from inventory.models import Inventory, TransactionList

delivery_columns = ['inventaire', 'date de création', 'validé ?']

class Delivery(TransactionList):
    inventory = models.ForeignKey(Inventory, on_delete=models.PROTECT, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    is_validated = models.BooleanField(default=False)
