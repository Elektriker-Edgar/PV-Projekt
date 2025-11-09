from django.template.loader import render_to_string
from django.http import HttpResponse
from .helpers import infer_inverter_class_key


def generate_quote_pdf(quote):
    """Generiere PDF für Angebot (vereinfacht - erstmal HTML)"""
    
    # HTML-Template rendern
    html_content = render_to_string('quotes/quote_pdf.html', {
        'quote': quote,
        'items': quote.items.all(),
        'customer': quote.precheck.site.customer,
        'site': quote.precheck.site,
    })
    
    # Für jetzt geben wir HTML zurück, später kann WeasyPrint konfiguriert werden
    return html_content.encode('utf-8')


def calculate_quote_pricing(precheck):
    """Berechne Angebotspreis basierend auf Precheck-Daten"""
    
    # Basis-Preislogik (vereinfacht)
    base_price = 500.0  # Grundpreis
    
    # WR-Klassen-Aufschlag
    inverter_prices = {
        '1kva': 800,
        '3kva': 1200,
        '5kva': 1800,
        '10kva': 2800,
    }
    
    inverter_key = infer_inverter_class_key(precheck.desired_power_kw or 0)
    price = base_price + inverter_prices.get(inverter_key, 1200)
    
    # Speicher-Aufschlag
    if precheck.storage_kwh:
        price += float(precheck.storage_kwh) * 600  # 600€/kWh
    
    # Netzform-Aufschlag
    if precheck.site.grid_type == 'TT':
        price += 200
    
    # Entfernungs-Aufschlag
    if precheck.site.distance_meter_to_hak > 10:
        price += (float(precheck.site.distance_meter_to_hak) - 10) * 15  # 15€/m
    
    # Eigene Komponenten Rabatt
    if precheck.own_components:
        price *= 0.8  # 20% Rabatt
    
    return round(price, 2)
