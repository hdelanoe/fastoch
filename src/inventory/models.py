from django.db import models

from provider.models import Provider

class Container(models.Model):
    name = models.CharField(max_length=32, default="My Container", unique=True)

    class Meta:
        abstract = True


class Product(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, blank=True, null=True)
    ean = models.BigIntegerField(unique=True, blank=True, null=True)
    multicode = models.CharField(max_length=16, unique=True, blank=True, null=True)
    description = models.CharField(max_length=64, blank=True, null=True)
    achat_ht = models.FloatField(default=0.00)
    is_new=models.BooleanField(default=True)
    has_changed=models.BooleanField(default=False)
    multicode_generated=models.BooleanField(default=False)

    def get_format_achat_ht(self):
        return format(self.achat_ht, '.2f')


class iProduct(models.Model):
    container_name = models.CharField(max_length=32, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)


    def as_dict(self):
        return {
            "NOM_FOURNISSEUR": self.product.provider,
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
        return f'{self.product.provider} {self.product.multicode} {self.product.description} { self.quantity} {self.product.achat_ht}'


class Inventory(Container):
    last_response =  models.TextField(default="Comment puis-je vous aider ?")
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f'name:{self.name}'
    
class Receipt(Container):
    is_waiting = models.BooleanField(default=True)    
