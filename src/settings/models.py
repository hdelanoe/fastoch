from django.db import models

class Settings(models.Model):
    pagin = models.IntegerField(default=25)
