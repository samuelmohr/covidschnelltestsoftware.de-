from django.shortcuts import render,redirect
from chrome.models import Selector
from kunden.models import Kunde
from django.http import JsonResponse
from django.forms.models import model_to_dict


# Create your views here.
def activate(request, kunden_id):
    # Selector
    list=Selector.objects.all()
    for el in list:
        el.delete()
    
    
    o=Selector()
    o.active=kunden_id
    o.save()
    
    return redirect('https://apo-portal.oesterreich-testet.at/SingleScreeningStation')







def data(request):
    # active
    list=Selector.objects.all()
    if(len(list)!=1):
        return ""
    
    nr=list[0].active

    kunde = None
    #get object
    try:
        kunde = Kunde.objects.get(pk=nr)
    except Kunde.DoesNotExist:
        print("no int id")
        kunden = Kunde.objects.all()
        for k in kunden:
            if k.id() == nr:
                kunde=k
                break
    if kunde== None:
        return ""
    

    return JsonResponse(model_to_dict(kunde))
