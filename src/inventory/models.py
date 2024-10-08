from django.db import models

Kesia2_column_names = {
    "fournisseur": "NOM_FOURNISSEUR",
    "ean": "EAN",
    "description": "DEF",
    "quantity": "STOCK",
    "achat_brut": "BaseHT",
    "achat_tva": "TAUX_TVA_ACHAT",
    "achat_net": "PRIX_ACHAT_TTC",
    "vente_net": "PRIX_TTC",
    "vente_tva": "TAUX_TVA_VENTE",
}

class Provider(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    n_tva = models.CharField(max_length=13, unique=True, blank=True, null=True)
    tva = models.FloatField(default=20.0, blank=True, null=True)

class Product(models.Model):
     
    class IncrementalChoices(models.TextChoices):
        QUANTITY = "quantity", "Quantity"
        WEIGHT = "weight", "Weight"

    class Unit(models.TextChoices):
        PIECE = "PIECE", "Piece"
        KG = "KG", "Kg"  

    fournisseur = models.ForeignKey(Provider, on_delete=models.PROTECT, blank=True, null=True)
    ean = models.BigIntegerField(unique=True, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    achat_brut = models.FloatField(blank=True, null=True)
    achat_net = models.FloatField(blank=True, null=True)
    achat_tva = models.FloatField(blank=True, null=True)
    coef_marge = models.FloatField(blank=True, null=True)
    vente_net = models.FloatField(blank=True, null=True)
    vente_tva = models.FloatField(blank=True, null=True)

    incremental_option = models.CharField(max_length=20, choices=IncrementalChoices, default=IncrementalChoices.WEIGHT)
    
    def __str__(self):
        return f'{self.fournisseur} {self.ean} {self.description} {self.quantity}'
    
    def as_Kesia2_dict(self):
        return {
            "NOM_FOURNISSEUR": self.fournisseur.name,
            "EAN": self.ean,
            "DEF": self.description,
            "STOCK": self.quantity,
            "BaseHT": self.achat_brut,
            "TAUX_TVA_ACHAT": self.achat_tva,
            "PRIX_ACHAT_TTC": self.achat_net,
            "PRIX_TTC": self.vente_net,
            "TAUX_TVA_VENTE": self.vente_tva,
        }

class StockTransaction(models.Model):

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

    def __str__(self):
        return f'{self.product.description} {self.quantity} {self.transaction_type} {self.date_transaction}'
    
    
class Inventory(models.Model):
    name = models.CharField(max_length=50, default="My Inventory", unique=True)
    products = models.ManyToManyField(Product)
    transaction_list = models.ManyToManyField(StockTransaction)
    last_response =  models.TextField(default="Comment puis-je vous aider ?")

    def __str__(self):
        return f'name:{self.name}'
    
 