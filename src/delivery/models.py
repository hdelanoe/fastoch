from django.db import models

from inventory.models import Inventory, Provider, TransactionList

delivery_columns = ['providers', 'inventaire', 'date de création', 'validé ?']

class Delivery(TransactionList):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, null=True)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    is_validated = models.BooleanField(default=False)
    