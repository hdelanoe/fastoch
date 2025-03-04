from django.db import models
from django.utils import timezone

from provider.models import Provider

class Inventory(models.Model):
    name = models.CharField(max_length=32, default="My Inventory", unique=True)
    is_current = models.BooleanField(default=False)
    is_waiting = models.BooleanField(default=True)

    def __str__(self):
        return f'name:{self.name}'

class Product(models.Model):
    ean = models.BigIntegerField(unique=True, blank=True, null=True)
    multicode = models.CharField(max_length=13, unique=True, blank=True, null=True)
    description = models.CharField(max_length=64, blank=True, null=True)
    achat_ht = models.FloatField(default=0.00)
    is_new=models.BooleanField(default=True)
    has_changed=models.BooleanField(default=False)
    multicode_generated=models.BooleanField(default=False)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, related_name='products', blank=True, null=True)


    def get_format_achat_ht(self):
        return format(self.achat_ht, '.2f')

    def __str__(self):
        return f'{self.multicode} {self.ean} {self.description} {self.achat_ht} {self.is_new} {self.has_changed} {self.multicode_generated}'

class iProduct(models.Model):
    quantity = models.IntegerField(default=0)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='iproducts', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='iproducts')

    def as_dict(self):
        return {
            "NOM_FOURNISSEUR": self.product.provider.name if self.product.provider else 'Unknown',  # Handle None case,
            "EAN": self.product.ean,
            "Code": self.product.multicode,
            "DEF": self.product.description,
            "STOCK": self.quantity,
            "PMPA": self.product.achat_ht,
        }

    def as_receipt(self):
        return {
            "Code": self.product.multicode,
            "STOCK": self.quantity,
        }

    def __str__(self):
        return f'{self.product.multicode} {self.product.provider.name} {self.product.ean} {self.product.description} { self.quantity} {self.product.achat_ht}'

class DLC(models.Model):
    iproduct = models.ForeignKey(iProduct, related_name='dates', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now().date())