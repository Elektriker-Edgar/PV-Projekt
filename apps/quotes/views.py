from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.utils import timezone
from .models import Quote, Precheck
from .forms import PrecheckForm
from .utils import generate_quote_pdf


def home(request):
    """Startseite mit Hero und 3-Schritte-Ablauf"""
    return render(request, 'quotes/home.html')


def precheck_wizard(request):
    """Vorprüfungs-Formular (Multi-Step)"""
    if request.method == 'POST':
        form = PrecheckForm(request.POST, request.FILES)
        if form.is_valid():
            precheck = form.save()
            messages.success(request, 'Ihre Vorprüfung wurde erfolgreich eingereicht. Wir melden uns binnen 24 Stunden bei Ihnen.')
            return render(request, 'quotes/precheck_success.html', {'precheck': precheck})
    else:
        form = PrecheckForm()
    
    return render(request, 'quotes/precheck_wizard.html', {'form': form})


def quote_detail(request, quote_number):
    """Angebots-Detail für Kunden"""
    quote = get_object_or_404(Quote, quote_number=quote_number, status__in=['sent', 'accepted'])
    return render(request, 'quotes/quote_detail.html', {'quote': quote})


def quote_pdf(request, quote_number):
    """PDF-Download für Angebot"""
    quote = get_object_or_404(Quote, quote_number=quote_number, status__in=['sent', 'accepted'])
    
    try:
        pdf_content = generate_quote_pdf(quote)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Angebot_{quote.quote_number}.pdf"'
        return response
    except Exception as e:
        raise Http404("PDF konnte nicht generiert werden.")
