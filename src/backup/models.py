from django.db import models

from inventory.models import Inventory

backup_columns = ['inventaire', 'date']

class Backup(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.PROTECT, null=True)
    products_backup = models.TextField()   
    transactions_backup = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)   
