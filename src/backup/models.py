from django.db import models

backup_columns = ['inventaire', 'date']

class Backup(models.Model):
    inventory_name = models.CharField(max_length=50)
    products_backup = models.TextField()   
    transactions_backup = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)   
