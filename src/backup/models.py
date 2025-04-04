from django.db import models

from inventory.models import Inventory

backup_columns = ['inventaire', 'date', 'type de sauvegarde']

class Backup(models.Model):

    class BackupType(models.TextChoices):
        MANUAL = "MANUAL", "Manuel"
        AUTO = "AUTO", "Automatique"

    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    iproducts_backup = models.JSONField()
    date_creation = models.DateTimeField(auto_now_add=True)
    backup_type = models.CharField(max_length=20, choices=BackupType, default=BackupType.MANUAL)
