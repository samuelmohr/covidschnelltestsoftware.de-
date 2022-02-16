from django.db import models

# Create your models here.
class Kunde(models.Model):
    anrede = models.CharField(max_length=20,blank=True, default="")
    vorname = models.CharField(max_length=200,blank=True, default="")
    nachname = models.CharField(max_length=200)
    sozialversicherungsnummer = models.CharField(max_length=20,primary_key=True )
    geburtsdatum = models.DateField(null=True)
    versicherung = models.CharField(max_length=40,blank=True, default="")
    adresse = models.CharField(max_length=200,blank=True, default="")
    plz = models.CharField(max_length=10,blank=True, default="")
    ort = models.CharField(max_length=100,blank=True, default="")
    telefon = models.CharField(max_length=100,blank=True, default="")
    email = models.EmailField(max_length=100,blank=True, default="")
    bemerkungen = models.CharField(max_length=500,blank=True, default="")
    termin = models.DateTimeField()
    
    class Kommunikationswege(models.TextChoices):
        SMS = 'SMS', 'SMS an die oben angegebene Telefonnummer'
        EMAIL = 'Email', 'Schriftliche Bestätigung als PDF an die oben angegbene Emailadresse'
        VORORT = 'vor Ort', 'Abholung in der Apotheke'
    kommunikation = models.CharField(max_length=10,choices=Kommunikationswege.choices,default=Kommunikationswege.SMS)
    
    active = models.BooleanField(default=False)
    informiert = models.BooleanField(default=False)
    
    testzeit = models.DateTimeField(null=True)
    positive = models.BooleanField(null=True,default=None)
    
    def __str__(self):
        return self.nachname + ", " + self.vorname + "  - " + self.sozialversicherungsnummer
    
    def anschrift(self):
        return self.adresse + ", " + self.plz + " " + self.ort
        
    def id(self):
        if self.sozialversicherungsnummer.isdigit():
            return self.sozialversicherungsnummer
        return abs(hash(self.sozialversicherungsnummer))
        
    class Meta:
        verbose_name = 'Kundenverwaltung'
        verbose_name_plural = 'Liste aller von Etermin synchronisierten Kunden'

