from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Quote, Precheck
from .forms import PrecheckForm, ExpressPackageForm
from .utils import generate_quote_pdf
from .calculation import create_quote_from_precheck
from .pricing import pricing_input_from_precheck, calculate_pricing


FILE_UPLOAD_FIELDS = (
    'meter_cabinet_photo',
    'hak_photo',
    'location_photo',
    'cable_route_photo',
)


def _collect_uploaded_files(files):
    """
    Normalisiert Mehrfach-Uploads zu einem Dict[str, list[UploadedFile]].
    """
    collected = {}
    for field in FILE_UPLOAD_FIELDS:
        file_list = files.getlist(field)
        if file_list:
            collected[field] = file_list
    return collected


def home(request):
    """Startseite mit Hero und 3-Schritte-Ablauf"""
    return render(request, 'quotes/home.html')


def precheck_wizard(request):
    """Vorprüfungs-Formular (Multi-Step)"""
    if request.method == 'POST':
        form = PrecheckForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_files = _collect_uploaded_files(request.FILES)
            precheck = form.save(uploaded_files=uploaded_files)
            
            # Automatische Angebotserstellung
            try:
                quote, pricing = create_quote_from_precheck(precheck.id)
                customer = precheck.site.customer
                customer.last_quote_number = quote.quote_number
                customer.save(update_fields=['last_quote_number'])
                messages.success(request, 
                    f'Ihre Vorprüfung wurde erfolgreich eingereicht. '
                    f'Angebot {quote.quote_number} wurde erstellt und wird geprüft. '
                    f'Wir melden uns binnen 24 Stunden bei Ihnen.')
                return render(request, 'quotes/precheck_success.html', {
                    'precheck': precheck,
                    'quote': quote,
                    'pricing': pricing
                })
            except Exception as e:
                pricing = calculate_pricing(pricing_input_from_precheck(precheck))
                messages.success(request, 'Ihre Vorprüfung wurde erfolgreich eingereicht. Wir melden uns binnen 24 Stunden bei Ihnen.')
                return render(request, 'quotes/precheck_success.html', {'precheck': precheck, 'pricing': pricing, 'quote': None})
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


def package_inquiry(request, package):
    """Express-Paket-Formular"""
    # Validiere Paket
    valid_packages = ['basis', 'plus', 'pro']
    if package not in valid_packages:
        messages.error(request, 'Ungültiges Paket ausgewählt.')
        return redirect('quotes:package_select')

    # Paketinformationen laden
    package_names = {
        'basis': 'Basis-Paket',
        'plus': 'Plus-Paket',
        'pro': 'Pro-Paket'
    }

    # Legacy: Package prices are now handled via Product catalog
    package_price = {'basis': 890, 'plus': 1490, 'pro': 2290}.get(package, 0)

    if request.method == 'POST':
        form = ExpressPackageForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_files = _collect_uploaded_files(request.FILES)
            precheck = form.save(package_choice=package, uploaded_files=uploaded_files)

            messages.success(request,
                f'Ihre Anfrage für das {package_names[package]} wurde erfolgreich eingereicht. '
                f'Wir melden uns binnen 24 Stunden bei Ihnen.')
            return redirect('quotes:package_success')
    else:
        form = ExpressPackageForm()

    return render(request, 'quotes/package_inquiry.html', {
        'form': form,
        'package': package,
        'package_name': package_names[package],
        'package_price': package_price
    })


def package_success(request):
    """Success-Seite nach Express-Paket-Anfrage"""
    return render(request, 'quotes/package_success.html')
