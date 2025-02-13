from django.db import models

provider_columns = ['Nom', 'Code']

class Provider(models.Model):
    name = models.CharField(max_length=32, blank=True, null=True)
    code = models.CharField(max_length=4, blank=True, null=True)
    erase_multicode = models.BooleanField(default=True)
    columns = ['Nom', 'Code']

    def __str__(self):
        return f'{self.name} {self.code} {self.erase_multicode}'