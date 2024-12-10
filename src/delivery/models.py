from django.db import models

from inventory.models import Provider

delivery_columns = ['providers', 'date de livraison', 'validé ?']

class Delivery(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True)
    date_time = models.DateTimeField(auto_now_add=True)
    is_validated = models.BooleanField(default=False)
    