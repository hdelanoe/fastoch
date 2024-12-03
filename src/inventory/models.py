from django.db import models

from provider.models import Provider

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



class Transaction(models.Model):

    iproduct = models.ForeignKey(iProduct, on_delete=models.CASCADE)
    date_transaction = models.DateTimeField(auto_now_add=True)

    def as_dict(self):
        return {
            "iproduct": self.iproduct,
            "quantity": self.iproduct.quantity,
            "date_transaction": self.date_transaction,
        }

    def as_Kesia2_inventory_dict(self):
        return {
            "Designation": self.iproduct.product.description,
            "MultiCode": self.iproduct.product.multicode,
            "Qté Mouv.": self.iproduct.quantity,
            "PMPA": self.iproduct.product.achat_ht,
        }

    def __str__(self):
        return f'{self.iproduct.product.description} {self.iproduct.quantity} {self.date_transaction}'

class iProductList(models.Model):
    iproducts = models.ManyToManyField(iProduct)

    class Meta:
        abstract = True

class TransactionList(models.Model):
    transactions = models.ManyToManyField(Transaction)

    class Meta:
        abstract = True


class Inventory(iProductList):
    name = models.CharField(max_length=32, default="My Inventory", unique=True)
    transaction_list = models.ManyToManyField(Transaction)
    last_response =  models.TextField(default="Comment puis-je vous aider ?")
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f'name:{self.name}'
    
class Receipt(iProductList):
    name = models.CharField(max_length=32, default="Reception en attente", unique=True)
    is_waiting = models.BooleanField(default=True)    
