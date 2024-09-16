from django.db import models
from customers.models import Customer


Pronatura_dictionary = {
    "name": "Nom",
    "quantity": "Nb Colis / Pièce",
    "lot_id": "N° lot",
    "description": "Désignation",
    "weight": "Poids net / brut",
    "price": "Prix",
    "discount": "% remise",
    "net_price": "Prix Net",
    "unit": "U",
    "tva": "% TVA",
    "net": "Montant net H.T.",
}

class InventoryDataType(models.Model):
    class DataTypeChoices(models.TextChoices):
        QUANTITY = "quantity", "Quantity"
        NAME = "name", "Name"
        WEIGHT = "weight", "Weight"
        PRICE = "price", "Price"
    
    data_type = models.CharField(max_length=20, choices=DataTypeChoices)

class Product(models.Model):
     
    class IncrementalChoices(models.TextChoices):
        QUANTITY = "quantity", "Quantity"
        WEIGHT = "weight", "Weight"

    class Unit(models.TextChoices):
        PIECE = "PIECE", "Piece"
        COLIS = "COLIS", "Colis"
        KG = "KG", "Kg"  
        G = "G", "Grammes"    

    quantity = models.IntegerField(blank=True, null=True)
    lot_id = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    discount = models.FloatField(blank=True, null=True)
    net_price = models.FloatField(blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    tva = models.FloatField(blank=True, null=True)
    net = models.FloatField(blank=True, null=True)

    incremental_option = models.CharField(max_length=20, choices=IncrementalChoices, default=IncrementalChoices.WEIGHT)
    
    extra_field_1 = models.CharField(max_length=100, blank=True, null=True)
    extra_field_2 = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f'{self.name} {self.price}'
    
    def to_dict(self):
        return {
            Pronatura_dictionary.get('quantity'): self.quantity,
            Pronatura_dictionary.get('lot_id'): self.lot_id,
            Pronatura_dictionary.get('name'): self.name,
            Pronatura_dictionary.get('description'): self.description,
            Pronatura_dictionary.get('weight'): self.weight,
            Pronatura_dictionary.get('price'): self.price,
            Pronatura_dictionary.get('discount'): self.discount,
            Pronatura_dictionary.get('net_price'): self.net_price,
            Pronatura_dictionary.get('unit'): self.unit,
            Pronatura_dictionary.get('tva'): self.tva,
            Pronatura_dictionary.get('net'): self.net,
        }

class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

class Inventory(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    entry_list = models.ManyToManyField(StockEntry)
    name = models.CharField(max_length=100, default="My Inventory")
    dtypes = models.ManyToManyField(InventoryDataType)
    dtypes_array = models.TextField(help_text="data types, seperated by new line", blank=True, null=True)

    def get_dtypes_as_list(self):
        if not self.dtypes_array:
            return []
        return [x.strip() for x in self.dtypes_array.split(",")]
    



class StockTransaction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    transaction_type = models.CharField(max_length=10)  # 'in' or 'out'
    date_transaction = models.DateTimeField(auto_now_add=True)
