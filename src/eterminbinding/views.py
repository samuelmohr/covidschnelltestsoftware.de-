from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse

from kunden.models import Kunde
from eterminbinding.models import EterminZugangsdaten, SyncDates

import requests
import datetime

# Create your views here.
def updateClient(dataset):
    try:
        if len(dataset["Additional1"])<=1:
            return
    except:
        return
    
    try:
        o=Kunde.objects.get(sozialversicherungsnummer=dataset["Additional1"])
        try:
            termin = timezone.make_aware(datetime.datetime.fromisoformat(dataset["StartDateTime"]))
        except:
            return
        
        if (termin!=timezone.get_current_timezone().normalize(o.termin)):
            o.delete()
            o=Kunde()

    except Kunde.DoesNotExist:    
        o=Kunde()
        
    o.anrede = dataset["Salutation"]
    if o.anrede == None:
        o.anrede = ""
    o.vorname = dataset["FirstName"]
    o.nachname = dataset["LastName"]
    o.sozialversicherungsnummer = dataset["Additional1"]
    try:
        o.geburtsdatum = datetime.datetime.strptime(dataset["Birthday"],"%d.%m.%Y").date()
    except:
        o.geburtsdatum = None
    o.versicherung = dataset["Additional2"]
    if o.versicherung == None:
        o.versicherung = ""
    o.adresse = dataset["Street"]
    if o.adresse == None:
        o.adresse = ""
    o.plz = dataset["ZIP"]
    if o.plz == None:
        o.plz = ""
    o.ort = dataset["Town"]
    if o.ort == None:
        o.ort = ""
    o.telefon = dataset["Phone"]
    if o.telefon == None:
        o.telefon = ""
    o.email = dataset["Email"]
    if o.email == None:
        o.email = ""
    o.bemerkungen = dataset["Notes"]
    if o.bemerkungen == None:
        o.bemerkungen = ""
    try:
        o.termin = timezone.make_aware(datetime.datetime.fromisoformat(dataset["StartDateTime"]))
    except:
        return
    
    choice = dataset["Additional3"].strip().lower()
    for p in Kunde.Kommunikationswege.choices:
        if (choice == p[1].lower() or choice == p[0].lower()):
            o.kommunikation = p[0]
            
    o.save()


def sync(request):
    #not logined
    if not request.user.is_authenticated:
        return redirect('admin:login')

    # sync
    list=EterminZugangsdaten.objects.all()
    if(len(list)!=1):
        return HttpResponse('<h1>Etermin Zugangsdaten fehlen</h1><p><a href="'+reverse("admin:eterminbinding_eterminzugangsdaten_changelist")+'" >Einstellungen</a></p>')
    
    zugang=list[0]
    
    r =requests.get('https://www.etermin.net/api/appointment', 
                    headers={"publickey":zugang.oeffentlicherSchluessel, "salt":zugang.salt, "signature":zugang.signature},
#                    params={"start":timezone.now().date().isoformat(),}
                    params={"start":timezone.now().date().isoformat(),"end":(timezone.now()+datetime.timedelta(days=1)).date().isoformat()}
            )
    
    if not r.ok:
        return HttpResponse('<h1>Sync mit Etermin misslungen!</h1><p><a href="'+ reverse("index") +'" >zurück</a></p>')
    
    for kunde in r.json():
        updateClient(kunde)
    
    o=SyncDates()
    o.syncdate=timezone.now().date()
    o.save()
    
    #sync ok page
    return HttpResponse('<h1>Sync mit Etermin war erfolgreich</h1><p><a href="'+ reverse("index") +'" >zurück</a></p>')
