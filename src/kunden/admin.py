from django.contrib import admin

from .models import *


class KundenAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (('termin','sozialversicherungsnummer'),),
        }),
        ('Kundendaten', {
            'fields': ('anrede',('vorname','nachname'),'geburtsdatum'),
        }),
        ('Kontakt', {
            'fields': ('kommunikation',('telefon','email'),('adresse','plz','ort')),
        }),
        ('Sonstiges', {
            'fields': ('versicherung', 'bemerkungen'),
        }),
    )
        
# Register your models here.
admin.site.register(Kunde,KundenAdmin)
