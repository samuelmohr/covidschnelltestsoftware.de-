from django.db import models

# Create your models here.
class Selector(models.Model):
    active = models.IntegerField()
