from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Quote, Precheck
from .forms import PrecheckForm
from .utils import generate_quote_pdf
from .calculation import create_quote_from_precheck


def home(request):
    """Startseite mit Hero und 3-Schritte-Ablauf"""
    return render(request, 'quotes/home.html')


def precheck_wizard(request):
    """Vorprüfungs-Formular (Multi-Step)"""
    if request.method == 'POST':
        form = PrecheckForm(request.POST, request.FILES)
        if form.is_valid():
            precheck = form.save()
            
            # Automatische Angebotserstellung
            try:
                quote = create_quote_from_precheck(precheck.id)
                messages.success(request, 
                    f'Ihre Vorprüfung wurde erfolgreich eingereicht. '
                    f'Angebot {quote.quote_number} wurde erstellt und wird geprüft. '
                    f'Wir melden uns binnen 24 Stunden bei Ihnen.')
                return render(request, 'quotes/precheck_success.html', {
                    'precheck': precheck,
                    'quote': quote
                })
            except Exception as e:
                # Fallback falls Kalkulation fehlschlägt
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


def faq(request):
    """FAQ-Seite mit häufigen Fragen zu PV-Anlagen"""
    return render(request, 'quotes/faq.html')


def packages(request):
    """Pakete & Preise Seite mit Leistungspaketen"""
    return render(request, 'quotes/packages.html')


def compatible_systems(request):
    """Kompatible Systeme - White-List getesteter WR/Speicher"""
    return render(request, 'quotes/compatible_systems.html')


@require_POST
def approve_quote(request, quote_id):
    """Angebot freigeben (Admin-Funktion)"""
    try:
        quote = get_object_or_404(Quote, id=quote_id, status='review')
        quote.status = 'approved'
        quote.approved_by = request.user
        quote.approved_at = timezone.now()
        quote.save()
        
        messages.success(request, f'Angebot {quote.quote_number} wurde freigegeben.')
        return JsonResponse({'status': 'success', 'message': 'Angebot freigegeben'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def precheck_success(request):
    """Success-Seite nach Vorprüfung"""
    return render(request, 'quotes/precheck_success.html')


def quote_review_list(request):
    """Liste der Angebote zur Freigabe (Admin)"""
    quotes_to_review = Quote.objects.filter(status='review').order_by('-created_at')
    return render(request, 'quotes/quote_review_list.html', {
        'quotes': quotes_to_review
    })
