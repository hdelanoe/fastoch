from django.db import models
from customers.models import Customer


class Product(models.Model):
    attributes = models.CharField(blank=True, null=True)
    quantity = models.IntegerField(default=0)
    lot_id = models.CharField(max_length=10, default="L000000000")
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    weight = models.FloatField(default=0.00)
    price = models.FloatField(default=0.00)
    unit = models.CharField(max_length=5, blank=True, null=True)
    tva = models.FloatField(default=0.00)
    net = models.FloatField(default=0.00)
    def __str__(self):
        return self.name

class Inventory(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    name = models.CharField(max_length=100, default="My Inventory")
    attributes = models.CharField(blank=True, null=True)

class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)

class StockTransaction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    transaction_type = models.CharField(max_length=10)  # 'in' or 'out'
    date_transaction = models.DateTimeField(auto_now_add=True)
