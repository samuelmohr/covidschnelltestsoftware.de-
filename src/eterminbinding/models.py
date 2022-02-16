from django.db import models

# Create your models here.

class EterminZugangsdaten(models.Model):
    privaterSchluessel =  models.CharField(max_length=100) 
    oeffentlicherSchluessel =  models.CharField(max_length=100) 
    salt =  models.CharField(max_length=100) 
    signature =  models.CharField(max_length=100) 
    def __str__(self):
        return "Etermin Zugang mit " + self.oeffentlicherSchluessel
    

    class Meta:
        verbose_name = 'Etermin Zugangsdaten'
        verbose_name_plural = 'Zugangsdaten zu Etermin'


class SyncDates(models.Model):
    syncdate= models.DateField(primary_key=True)
