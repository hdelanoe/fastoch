from django.db import models

provider_columns = ['Nom', 'Code']

class Provider(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    #n_tva = models.CharField(max_length=13, unique=True, blank=True, null=True)
    #tva = models.FloatField(default=20.0, blank=True, null=True)
    code = models.CharField(max_length=4, blank=True, null=True)
    columns = ['Nom', 'Code']