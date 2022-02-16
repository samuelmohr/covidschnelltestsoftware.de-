from django.db import models

# Create your models here.

class EmailZugangsdaten(models.Model):
    smtp = models.CharField(max_length=100) 
    port = models.IntegerField(default=0)
    login = models.CharField(max_length=100,null=True,blank=True,default=None) 
    password = models.CharField(max_length=100,null=True,blank=True,default=None) 
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    mailfrom = models.CharField(max_length=100) 
    
    def __str__(self):
        return "Zugang zu " + self.smtp
    
    class Meta:
        verbose_name = 'Email Zugangsdaten'
        verbose_name_plural = 'Email Zugangsdaten'

class SMSZugangsdaten(models.Model):
    key = models.CharField(max_length=100) 
    sender = models.CharField(max_length=100,null=True,blank=True,default=None) 
    def __str__(self):
        return "Zugang zu cm.com mit " + self.key
    
    class Meta:
        verbose_name = 'SMS Zugangsdaten'
        verbose_name_plural = 'SMS Zugangsdaten'
