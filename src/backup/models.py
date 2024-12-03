from django.db import models

from inventory.models import iProductList

backup_columns = ['inventaire', 'date', 'type de sauvegarde']

class Backup(models.Model):

    class BackupType(models.TextChoices):
        MANUAL = "MANUAL", "Manuel"
        AUTO = "AUTO", "Automatique"  

    iproduct_list_name = models.CharField(max_length=32, null=True)
    products_backup = models.JSONField()
    transactions_backup = models.JSONField(null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    backup_type = models.CharField(max_length=20, choices=BackupType, default=BackupType.MANUAL)
