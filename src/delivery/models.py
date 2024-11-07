from django.db import models

from inventory.models import Inventory, Provider, TransactionList

delivery_columns = ['fournisseurs', 'inventaire', 'date de création', 'validé ?']

class Delivery(TransactionList):
    inventory = models.ForeignKey(Inventory, on_delete=models.PROTECT, null=True)
    providers = models.ManyToManyField(Provider)
    date_creation = models.DateTimeField(auto_now_add=True)
    is_validated = models.BooleanField(default=False)
    