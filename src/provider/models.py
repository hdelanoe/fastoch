from django.db import models

provider_columns = ['Nom', 'N TVA Intracommunautaire', 'Taux TVA par défaut']

class Provider(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    n_tva = models.CharField(max_length=13, unique=True, blank=True, null=True)
    tva = models.FloatField(default=20.0, blank=True, null=True)
