from django.db import models

from provider.models import Provider

class Product(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, blank=True, null=True)
    ean = models.BigIntegerField(unique=True, blank=True, null=True)
    multicode = models.CharField(max_length=16, unique=True, blank=True, null=True)
    description = models.CharField(max_length=32, blank=True, null=True)
    quantity = models.IntegerField(default=0)
    achat_ht = models.FloatField(default=0.00)
    coef_marge = models.FloatField(blank=True, null=True)
    vente_net = models.FloatField(blank=True, null=True)

    has_changed=models.BooleanField(default=False)
    multicode_generated=models.BooleanField(default=False)
    is_new=models.BooleanField(default=False)

    def get_format_achat_ht(self):
        return format(self.achat_ht, '.2f')

    def as_dict(self):
        return {
            "NOM_FOURNISSEUR": self.provider,
            "EAN": self.ean,
            "Code": self.multicode,
            "DEF": self.description,
            "STOCK": self.quantity,
            "PMPA": self.achat_ht,
        }

    def __str__(self):
        return f'{self.provider} {self.multicode} {self.description} { self.quantity} {self.achat_ht}'

class Transaction(models.Model):

    class TransctionType(models.TextChoices):
        IN = "in", "In"
        OUT = "out", "Out"

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    transaction_type = models.CharField(max_length=3, choices=TransctionType, default=TransctionType.IN)
    date_transaction = models.DateTimeField(auto_now_add=True)

    def as_dict(self):
        return {
            "product": self.product,
            "quantity": self.quantity,
            "transaction_type": self.transaction_type,
            "date_transaction": self.date_transaction,
        }

    def as_Kesia2_inventory_dict(self):
        return {
            "Designation": self.product.description,
            "MultiCode": self.product.multicode,
            "Qté Mouv.": self.quantity,
            "PMPA": self.product.achat_ht,
        }

    def __str__(self):
        return f'{self.product.description} {self.quantity} {self.transaction_type} {self.date_transaction}'

class ProductList(models.Model):
    products = models.ManyToManyField(Product)

    class Meta:
        abstract = True

class TransactionList(models.Model):
    transactions = models.ManyToManyField(Transaction)

    class Meta:
        abstract = True


class Inventory(ProductList):
    name = models.CharField(max_length=50, default="My Inventory", unique=True)
    transaction_list = models.ManyToManyField(Transaction)
    last_response =  models.TextField(default="Comment puis-je vous aider ?")
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f'name:{self.name}'
    
class Receipt(ProductList):
    is_waiting = models.BooleanField(default=True)    
