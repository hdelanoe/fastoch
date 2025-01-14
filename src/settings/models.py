from django.db import models

class Settings(models.Model):
    erase_multicode = models.BooleanField(default=False)
