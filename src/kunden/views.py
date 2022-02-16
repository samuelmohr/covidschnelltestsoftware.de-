from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect

from django.db.models import Q

from .models import Kunde

from eterminbinding.models import SyncDates

# Create your views here.
def index(request):
    #not logined
    if not request.user.is_authenticated:
        return redirect('admin:login')
    
    #server sync
    try:
        SyncDates.objects.get(syncdate=timezone.now().date())
    except SyncDates.DoesNotExist:    
        return redirect('eterminsync')
    
    #client page

    context = {}
    searchstring = request.GET.get('search')
    if searchstring:
        context['searchstring'] = searchstring
        liste = Kunde.objects.all()
        
        for word in searchstring.split():
            liste = liste.filter(Q(nachname__icontains=word)|Q(vorname__icontains=word)|Q(sozialversicherungsnummer__icontains=word))
        
        
    else:
        #liste = Kunde.objects.order_by('termin')
        liste = Kunde.objects.filter(termin__gte=timezone.now().replace(hour=0, minute=0, second=0), termin__lte=timezone.now().replace(hour=23, minute=59, second=59)).order_by('nachname')
    
    context['kunden'] = liste
    
    return render(request, 'kunden.html', context)
    


def ergebnis(request, kunden_id):
    #not logined
    if not request.user.is_authenticated:
        return redirect('admin:login')

    kunde = None
    #get object
    try:
        kunde = Kunde.objects.get(pk=kunden_id)
    except Kunde.DoesNotExist:
        kunden = Kunde.objects.all()
        for k in kunden:
            if k.id() == kunden_id:
                kunde=k
                break
    if kunde== None:
        kunde = get_object_or_404(Kunde, pk=kunden_id)

    context = {'kunde':kunde, 'today': str(timezone.now()), 'positive' : False, 'notifier' : Kunde.Kommunikationswege.choices}

    if kunde.testzeit:
        context = {'kunde':kunde, 'today': str(timezone.get_current_timezone().normalize(kunde.testzeit).date()), 'time' : timezone.get_current_timezone().normalize(kunde.testzeit).strftime('%H:%M'), 'positive' : kunde.positive, 'notifier' : Kunde.Kommunikationswege.choices}
        
    return render(request, 'ergebnis.html', context)
