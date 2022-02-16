from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings

from django.core.mail import send_mail, EmailMessage
from django.core import mail
from django.core.mail.backends.smtp import EmailBackend
from django.template import loader


from kunden.models import Kunde

from .models import SMSZugangsdaten, EmailZugangsdaten

from django.utils import timezone
import datetime
from pathlib import Path
import io
import os

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from CMText.TextClient import TextClient
import phonenumbers
import requests
import subprocess

# Helper functions

def getMailBackend():
    
    # Zugangsdaten
    list=EmailZugangsdaten.objects.all()
    if(len(list)!=1):
        return None
    
    zugang=list[0]
    
    try:
        if(zugang.login and zugang.password):
            connection = EmailBackend(host=zugang.smtp,port=zugang.port,username=zugang.login,password=zugang.password,use_tls=zugang.use_tls,use_ssl=zugang.use_ssl)
        elif(zugang.login):
            connection = EmailBackend(host=zugang.smtp,port=zugang.port,username=zugang.login,use_tls=zugang.use_tls,use_ssl=zugang.use_ssl)
        elif(zugang.password):
            connection = EmailBackend(host=zugang.smtp,port=zugang.port,password=zugang.password,use_tls=zugang.use_tls,use_ssl=zugang.use_ssl)
        else:
            connection = EmailBackend(host=zugang.smtp,port=zugang.port,use_tls=zugang.use_tls,use_ssl=zugang.use_ssl)
        return connection
    except Exception as e:
        print(e)
        return None


def getSMSBackend():
    
    # Zugangsdaten
    list=SMSZugangsdaten.objects.all()
    if(len(list)!=1):
        return None
    
    zugang=list[0]
    
    try:
        connection = {'key':zugang.key, 'sender':zugang.sender}
        return connection
    except Exception as e:
        print(e)
        return None
    
def getMailFrom():
    # Zugangsdaten
    list=EmailZugangsdaten.objects.all()
    if(len(list)!=1):
        return ""
    
    zugang=list[0]
    
    return zugang.mailfrom
    
def generateResultPDF(kunde, mit_hinweis):
    try:
        packet = io.BytesIO()
        # create a new PDF with Reportlab
        can = canvas.Canvas(packet)
        can.setFont("Helvetica", 12) #choose your font type and font size
        can.drawString(80, 550, "Name (name):")
        can.drawString(80, 515, "Geburtsdatum (date of birth):")
        can.drawString(80, 480, "Versicherungsnummer:")
        can.drawString(80, 435, "Testabnahme Datum / Uhrzeit:") 
        can.drawString(80, 370, "Zum Zeitpunkt der Probenentnahme lautet das                             :")        
        
        can.setFont("Helvetica", 11) #choose your font type and font size
        can.drawString(80, 460, "(health insurance Number)")
        can.drawString(80, 415, "(date and time of testing)")        
        
        can.setFont("Helvetica", 12) #choose your font type and font size
        can.drawString(300, 550, kunde.vorname + " " + kunde.nachname)  
        if kunde.geburtsdatum:
            can.drawString(300, 515, kunde.geburtsdatum.strftime('%d.%m.%Y'))  
        can.drawString(300, 480, kunde.sozialversicherungsnummer)
        can.drawString(300, 435, timezone.get_current_timezone().normalize(kunde.testzeit).strftime('%d.%m.%y %H:%M')) 


        
        if kunde.positive:
            can.setFillColorRGB(1, 0, 0.1) #choose your font colour
            can.setFont("Helvetica-Bold", 12) #choose your font type and font size
            can.drawString(332, 370, "TESTERGEBNIS")   
            
            #can.setFont("Calibri", 30) #choose your font type and font size
            can.setFont("Helvetica-Bold", 24) #choose your font type and font size
            can.drawString(80, 310, "POSITIV") 
            #can.setFont("Calibri", 20) #choose your font type and font size
            can.setFont("Helvetica-Bold", 14) #choose your font type and font size
            can.drawString(180, 310, "auf COVID-19 mittels Antigenschnelltest") 
            
            can.setFillColorRGB(0,0,0) #choose your font colour
            can.setFont("Helvetica", 12) #choose your font type and font size
            can.drawString(100, 275, "(positive Antigen Rapid Test)") 

        else:
            can.setFillColorRGB(0.121, 0.305, 0.474) #choose your font colour
            can.setFont("Helvetica-Bold", 12) #choose your font type and font size
            can.drawString(332, 370, "TESTERGEBNIS")   
            
            #can.setFont("Calibri", 30) #choose your font type and font size
            can.setFont("Helvetica-Bold", 24) #choose your font type and font size
            can.drawString(80, 310, "NEGATIV") 
            #can.setFont("Calibri", 20) #choose your font type and font size
            can.setFont("Helvetica-Bold", 14) #choose your font type and font size
            can.drawString(190, 310, "auf COVID-19 mittels Antigenschnelltest") 
            
            can.setFillColorRGB(0,0,0) #choose your font colour
            can.setFont("Helvetica", 12) #choose your font type and font size
            can.drawString(100, 275, "(negative Antigen Rapid Test)") 

        can.save()

        
        #move to the beginning of the StringIO buffer
        packet.seek(0)
        new_pdf = PdfFileReader(packet)
        # read your existing PDF
        base_pdf = PdfFileReader(open("templates/ergebnis_frame.pdf", "rb"))
        comment_pdf = PdfFileReader(open("templates/hinweise.pdf", "rb"))
            
        output = PdfFileWriter()
        # add the "watermark" (which is the new pdf) on the existing page
        page = base_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        #page.mergePage(result_pdf.getPage(0))
        output.addPage(page)
        
        if mit_hinweis:
            output.addPage(comment_pdf.getPage(0))
                           
        # finally, write "output" to a real file
        outputStream = open('pdfs/ergebnis_'+str(kunde.id())+'.pdf', "wb")
        output.write(outputStream)
        outputStream.close()
              
    except Exception as e:
        print(e)
        return False       
        
    return True
    

def generateProtocolPDF(kunde):
    try:
        packet = io.BytesIO()
        # create a new PDF with Reportlab
        can = canvas.Canvas(packet)

        # Block 1.1
        can.setFont("Helvetica-Bold", 14) #choose your font type and font size
        can.drawString(80, 705, "VOM KUNDEN AUSZUFÜLLEN:")        

        can.setFont("Helvetica", 12) #choose your font type and font size
        can.drawString(80, 672, "Vorname:")
        can.drawString(300, 672, "Nachname:")
        can.drawString(80, 634, "Versicherungsnummer (10 Stellen):")
        can.drawString(80, 596, "Versichert bei:")
        can.drawString(80, 558, "Wohnanschrift:")
        can.drawString(80, 520, "Plz und Ort:")

        can.setFont("Helvetica-Bold", 12) #choose your font type and font size
        can.drawString(150, 672, kunde.vorname)
        can.drawString(380, 672, kunde.nachname)
        can.drawString(300, 634, kunde.sozialversicherungsnummer)
        can.drawString(200, 596, kunde.versicherung)
        can.drawString(200, 558, kunde.adresse)
        can.drawString(200, 520, kunde.plz + "  " + kunde.ort)

        # Block 1.1
        can.setFont("Helvetica", 12) #choose your font type and font size
        can.drawString(80, 480, "Testergebnisübermittlung via (bitte nur EINES ankreuzen)")
        can.line(80, 478, 387, 478)

        can.drawString(80, 450, "o SMS auf folgende Telefonnummer:")        
        can.drawString(80, 425, "o schriftliche Bestätigung (pdf) per Mail auf folgende Adresse:")        
        can.drawString(80, 400, "o Abholung in der Apotheke")                

        can.setFont("Helvetica-Bold", 12) #choose your font type and font size
        can.drawString(80, 370, "PRIVAT/KUF")        
        can.drawString(360, 370, "o kassiert (PZN: 8076528)")        
        
        can.setFont("Helvetica", 12) #choose your font type and font size
        can.drawString(160, 370, "versichert: 25€ privat kassieren!!!")      
        
        if kunde.kommunikation == Kunde.Kommunikationswege.SMS:
            can.drawString(80, 450, "x")  
        if kunde.kommunikation == Kunde.Kommunikationswege.EMAIL:
            can.drawString(80, 425, "x") 
        if kunde.kommunikation == Kunde.Kommunikationswege.VORORT:
            can.drawString(80, 400, "x")
            
        can.setFont("Helvetica-Bold", 12)
        can.drawString(320, 450, kunde.telefon)
        can.drawString(425, 425, kunde.email) 

        # Block 2
        can.setFont("Helvetica-Bold", 12) #choose your font type and font size
        can.drawString(80, 340, "VON DER TESTENDEN PERSON AUSZUFÜLLEN")        

        can.setFont("Helvetica", 11) #choose your font type and font size
        can.drawString(80, 315, "o symptomlos (Antigenschnelltests sind NUR FÜR SYMPTOMLOSE Personen erlaubt!)")        
        can.drawString(80, 295, "o KEIN Nasenbluten/ Nasenscheidenwandoperationen/ andere Operationen an der Nase/")        
        can.drawString(90, 280, "bekannte Polypen/ Blutverdünner (AUSGENOMMEN Acetylsalicylsäure)")        
        can.drawString(90, 265, "wenn ja: RACHENABSTRICH!")        


        can.setFont("Helvetica", 12) #choose your font type and font size
        can.drawString(80, 235, "Testabnahme Datum / Uhrzeit: .................................................................")        
        
        can.setFont("Helvetica-Bold", 14) #choose your font type and font size
        can.drawString(80, 210, "o      negativ auf COVID-19 mittels Antigenschnelltest")        
        can.drawString(80, 188, "o      positiv auf COVID-19 mittels Antigenschnelltest")        
        
        can.setFont("Helvetica", 12) #choose your font type and font size        
        can.drawString(80, 165, "Unterschrift durchführender Pharmazeut:")        
        can.drawString(80, 145, "o Nasopharyngeal        o Oropharyngeal")               
        
        # Block 3
        can.setFont("Helvetica-Bold", 12) #choose your font type and font size
        can.drawString(80, 120, "VOM LABORANTEN AUSZUFÜLLEN")        

        can.setFont("Helvetica", 12) #choose your font type and font size
        can.drawString(80, 93, "o Testergebnis mit Protokoll abfotografiert")        
        can.drawString(80, 75, "o Bestätigung übermittelt")        
       
        can.save()

        
        #move to the beginning of the StringIO buffer
        packet.seek(0)
        new_pdf = PdfFileReader(packet)
        # read your existing PDF
        base_pdf = PdfFileReader(open("templates/protokoll.pdf", "rb"))
            
        output = PdfFileWriter()
        # add the "watermark" (which is the new pdf) on the existing page
        page = base_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        #page.mergePage(result_pdf.getPage(0))
        output.addPage(page)
                                   
        # finally, write "output" to a real file
        outputStream = open('pdfs/protokoll_'+str(kunde.id())+'.pdf', "wb")
        output.write(outputStream)
        outputStream.close()
              
    except Exception as e:
        print(e)
        return False       
        
    return True



def notify_by_sms(request, kunde):
    
    # backend
    backend = getSMSBackend()
    if backend == None:
        return HttpResponse('<h1>SMS Provider Zugangsdaten fehlerhaft</h1><p><a href="'+reverse("admin:notifier_smszugangsdaten_changelist")+'" >Einstellungen</a></p>')

    client = TextClient(apikey=backend['key'])
    
    try:
        pn=phonenumbers.parse(kunde.telefon, 'AT')
        if not phonenumbers.is_valid_number(pn):
            raise Exception('no valid_number')
        phonenumber = "00"+str(pn.country_code)+str(pn.national_number)
    except Exception as e: 
        return HttpResponse('<h1>Kunde hat keine gültige Telefonnummer angegeben</h1><p><a href="'+reverse("admin:kunden_kunde_change",args=[kunde.sozialversicherungsnummer])+'" >Kunde bearbeiten</a> oder <a href="'+reverse("index")+'" >zurück zur Startseite</a></p>')
    
    # content
    template = loader.get_template('sms.txt')
    context = {
        'kunde': kunde,
    }
    
    try:
        client.SendSingleMessage(message=template.render(context, request), from_=backend['sender'], to=[phonenumber])
        
    except Exception as e:
        print(e)
        return HttpResponse('<h1>SMS Versandt fehlgeschlagen</h1><p><a href="'+reverse("admin:notifier_smszugangsdaten_changelist")+'" >Einstellungen</a> oder <a href="'+reverse("index")+'" >zurück</a></p>')

    kunde.informiert = True
    kunde.active = False
    kunde.save()
    return None

def notify_by_mail(request, kunde):
    
    # backend
    backend = getMailBackend()
    if backend == None:
        return HttpResponse('<h1>Email Zugangsdaten fehlerhaft</h1><p><a href="'+reverse("admin:notifier_emailzugangsdaten_changelist")+'" >Einstellungen</a></p>')


    # content
    template = loader.get_template('email.txt')
    context = {
        'kunde': kunde,
    }
    
    try:
        email = EmailMessage(
            subject = 'Testergebnis COVID-19 Antigenschnelltest',
            body = template.render(context, request),
            from_email = getMailFrom(),
            to = [kunde.email],
#            reply_to = [''],
            connection=backend
        )

        with Path('pdfs/ergebnis_'+str(kunde.id())+'.pdf').open('rb') as f:
            email.attach('Testergebnis.pdf', f.read(),"application/pdf")
        if not email.send():
            return HttpResponse('<h1>Kunde hat keine gültige Email Adresse angegeben</h1><p><a href="'+reverse("admin:kunden_kunde_change",args=[kunde.sozialversicherungsnummer])+'" >Kunde bearbeiten</a> oder <a href="'+reverse("index")+'" >zurück zur Startseite</a></p>')
    except Exception as e:
        print(e)
        return HttpResponse('<h1>Email Versandt fehlgeschlagen</h1><p><a href="'+reverse("admin:notifier_emailzugangsdaten_changelist")+'" >Einstellungen</a> oder <a href="'+reverse("index")+'" >zurück</a></p>')

    kunde.informiert = True
    kunde.active = False
    kunde.save()
    return None

def printPDF(filename):
    print(os.path.join(settings.BASE_DIR, filename))
    try:
         subprocess.call([os.path.join(settings.BASE_DIR, 'pdfs/PDFtoPrinter.exe'), os.path.join(settings.BASE_DIR, filename)])
    except Exception as e:
         print(e)
         return False
    return True


# Create your views here.

def notify(request, kunden_id):
    #not logined
    if not request.user.is_authenticated:
        return redirect('admin:login')

    #get object
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

    #add test result data
    try:
        testdate = datetime.datetime.fromisoformat(request.POST['testdatum']).date()
        testtime = datetime.datetime.strptime(request.POST['testzeit'],"%H:%M").time()
        test = timezone.make_aware(datetime.datetime.combine(testdate,testtime))
        invalidtest=False
    except: 
        invalidtest=True
        
    try:
        if(request.POST['ergebnis']=="1"):
            result = True
        else:
            result = False
    except: 
        invalidtest=False
    
    if(invalidtest):
        return HttpResponse('<h1>Ungültige Testdaten</h1><p>Kunde ist <b>nicht</b> benachrichtigt worden. <a href="'+reverse("testergebnis",args=[kunden_id])+'" >Testdaten aktualisieren</a> oder <a href="'+reverse("index")+'" >Startseite</a></p>')

    kunde.positive = result
    kunde.testzeit = test
    kunde.save()
    
    check_values = request.POST.getlist('choice[]')
    
    if len(check_values)<=0:
        return HttpResponse('<h1>Ungültige Testdaten</h1><p>Kunde ist <b>nicht</b> benachrichtigt worden. <a href="'+reverse("testergebnis",args=[kunden_id])+'" >Testdaten aktualisieren</a> oder <a href="'+reverse("index")+'" >Startseite</a></p>')
        
    for val in check_values:
        kommunikation = None
        for kom in  Kunde.Kommunikationswege:
            if val == kom.value:
                kommunikation = kom
            
        
        #generate PDF
        if kommunikation == Kunde.Kommunikationswege.VORORT:
            if not generateResultPDF(kunde,False):
                return HttpResponse('<h1>PDF Erstellung fehlgeschlagen</h1><p>Kunde ist <b>nicht</b> benachrichtigt worden. <a href="'+reverse("index")+'" >Startseite</a></p>')
            
        if kommunikation == Kunde.Kommunikationswege.EMAIL:
            if not generateResultPDF(kunde,True):
                return HttpResponse('<h1>PDF Erstellung fehlgeschlagen</h1><p>Kunde ist <b>nicht</b> benachrichtigt worden. <a href="'+reverse("index")+'" >Startseite</a></p>')
            
        
        #notify
        if kommunikation == Kunde.Kommunikationswege.EMAIL:
            ret = notify_by_mail(request,kunde)
            if ret != None:
                return ret
        
        if kommunikation == Kunde.Kommunikationswege.SMS:
            ret = notify_by_sms(request,kunde)
            if ret != None:
                return ret
    
        kunde.informiert = True
        kunde.active = False
        kunde.save()
        
        if kommunikation == Kunde.Kommunikationswege.VORORT:
            if not printPDF('pdfs/ergebnis_'+str(kunde.id())+'.pdf'):
                return HttpResponse('<h1>Drucken fehlgeschlagen</h1><p><a target="_blank" href="'+str(request.scheme)+'://'+request.get_host()+'/pdfs/ergebnis_'+ str(kunde.id()) + '.pdf">PDF</a> liegt im Ordnersystem. <a href="'+reverse("index")+'" >zurück</a></p>')
    
    return redirect('index')
    
    
    
def arrival(request, kunden_id):
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
        
    kunde.active=True
    kunde.save()

    #notify
    if not generateProtocolPDF(kunde):
        return HttpResponse('<h1>PDF Erstellung fehlgeschlagen</h1><p>Kunde gilt dennoch als anwesend. <a href="'+reverse("index")+'" >zurück</a></p>')
    
    if not printPDF('pdfs/protokoll_'+str(kunde.id())+'.pdf'):
        return HttpResponse('<h1>Drucken fehlgeschlagen</h1><p><a target="_blank" href="'+str(request.scheme)+'://'+request.get_host()+'/pdfs/protokoll_'+ str(kunde.id()) + '.pdf">PDF</a> liegt im Ordnersystem. <a href="'+reverse("index")+'" >zurück</a></p>')
    
    return redirect('index')
    
    
