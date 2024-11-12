from django.db import models

from provider.models import Provider

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
    quantity = models.IntegerField(default=0)
    achat_brut = models.FloatField(default=0.00)
    achat_net = models.FloatField(blank=True, null=True)
    achat_tva = models.FloatField(blank=True, null=True)
    coef_marge = models.FloatField(blank=True, null=True)
    vente_net = models.FloatField(blank=True, null=True)
    vente_tva = models.FloatField(blank=True, null=True)
    discount = models.FloatField(blank=True, null=True)
    code_art = models.CharField(max_length=16, unique=True, blank=True, null=True)

    has_changed=models.BooleanField(default=False)

    incremental_option = models.CharField(max_length=20, choices=IncrementalChoices, default=IncrementalChoices.WEIGHT)

    def get_format_achat_brut(self):
        return format(self.achat_brut, '.2f')

    def __str__(self):
        return f'{self.fournisseur} {self.ean} {self.description} {self.quantity}'

    def as_Kesia2_dict(self):
        return {
            "IDART": self.code_art,
            "NOM_FOURNISSEUR": self.fournisseur.name,
            "EAN": self.ean,
            "DEF": self.description,
            "STOCK": self.quantity,
            "BaseHT": self.achat_brut,
            #"TAUX_TVA_ACHAT": self.achat_tva,
            #"PRIX_ACHAT_TTC": self.achat_net,
            "PRIX_TTC": self.vente_net,
            #"TAUX_TVA_VENTE": self.vente_tva,
        }

    def as_Kesia2_dict_with_quantity(self, quantity):
        return {
            "IDART": self.code_art,
            "NOM_FOURNISSEUR": self.fournisseur.name,
            "EAN": self.ean,
            "DEF": self.description,
            "STOCK": quantity,
            "BaseHT": self.achat_brut,
            #"TAUX_TVA_ACHAT": self.achat_tva,
            #"PRIX_ACHAT_TTC": self.achat_net,
            "PRIX_TTC": self.vente_net,
            #"TAUX_TVA_VENTE": self.vente_tva,
        }

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

    def __str__(self):
        return f'name:{self.name}'
