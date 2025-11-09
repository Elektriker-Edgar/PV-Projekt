"""
Kalkulationslogik fÃ¼r PV-Anlagen basierend auf Blueprint-Anforderungen
"""
from decimal import Decimal
from typing import Dict, List, Tuple
from datetime import timedelta
from django.utils import timezone
from .models import Quote, QuoteItem, Component, Precheck, PriceConfig
from .pricing import pricing_input_from_precheck, calculate_pricing


class QuoteCalculator:
    """Automatisierte Angebotskalkulation nach Blueprint-Regeln"""
    
    # Basispakete aus Blueprint
    PACKAGES = {
        'basis': {
            'name': 'Basis',
            'base_price': Decimal('890.00'),
            'description': 'WR bis 3 kVA, AC-Anschluss, MaStR/Netzmeldung',
            'includes': [
                'wr_installation',
                'ac_wiring', 
                'commissioning',
                'mastr_registration',
                'grid_notification',
                'test_protocol'
            ]
        },
        'plus': {
            'name': 'Plus', 
            'base_price': Decimal('1490.00'),
            'description': 'Basis + ZÃ¤hlerplatz-ErtÃ¼chtigung + SPD',
            'includes': [
                'wr_installation',
                'ac_wiring',
                'meter_point_upgrade', 
                'spd_installation',
                'selectivity_check',
                'potential_equalization',
                'commissioning',
                'mastr_registration', 
                'grid_notification',
                'extended_documentation'
            ]
        },
        'pro': {
            'name': 'Pro',
            'base_price': Decimal('2290.00'), 
            'description': 'Plus + Speicherintegration + Energiemanagement',
            'includes': [
                'wr_installation',
                'ac_wiring',
                'meter_point_upgrade',
                'spd_installation', 
                'selectivity_check',
                'potential_equalization',
                'storage_integration',
                'energy_management',
                'network_integration',
                'monitoring_setup',
                'commissioning',
                'mastr_registration',
                'grid_notification', 
                'extended_documentation',
                'maintenance_12m'
            ]
        }
    }
    
    # Anfahrtskosten nach Zonen (Hamburg 0-60 km)
    TRAVEL_COSTS = {
        'zone_0': Decimal('0.00'),    # Hamburg
        'zone_30': Decimal('50.00'),  # bis 30km
        'zone_60': Decimal('95.00'),  # bis 60km
    }
    
    # ZuschlÃ¤ge
    SURCHARGES = {
        'netzform_tt': Decimal('150.00'),        # TT-Netz statt TN
        'selective_fuse': Decimal('220.00'),      # Selektive Vorsicherung
        'cable_length_extra': Decimal('25.00'),  # pro Meter Ã¼ber 15m
        'special_mounting': Decimal('180.00'),    # Besondere Montagesituation
    }
    
    # Rabatte  
    DISCOUNTS = {
        'complete_kit': Decimal('0.15'),  # 15% bei Komplett-Kit von EDGARD
        'referral': Decimal('0.05'),     # 5% Weiterempfehlung
    }
    
    def __init__(self, precheck: Precheck):
        """Initialisiert Calculator mit VorprÃ¼fungsdaten"""
        self.precheck = precheck
        self.site = precheck.site
        self.customer = self.site.customer
        
    def determine_package(self) -> str:
        """Bestimmt Paket basierend auf Anforderungen"""
        # Speicher â Pro
        if self.precheck.storage_kwh and self.precheck.storage_kwh > 0:
            return 'pro'
            
        # Leistung > 3kVA oder spezielle Anforderungen â Plus  
        if (self.precheck.desired_power_kw > 3 or 
            self.precheck.inverter_class in ['5kva', '10kva'] or
            self.site.grid_type == 'TT'):
            return 'plus'
            
        # Standard â Basis
        return 'basis'
    
    def calculate_travel_cost(self) -> Decimal:
        """Berechnet Anfahrtskosten basierend auf Entfernung"""
        # Vereinfacht: basierend auf PLZ oder Stadt
        # TODO: Echte Distanzberechnung implementieren
        city = self.site.city.lower() if hasattr(self.site, 'city') else ''
        
        if 'hamburg' in city:
            return self.TRAVEL_COSTS['zone_0']
        elif any(suburb in city for suburb in ['norderstedt', 'ahrensburg', 'pinneberg']):
            return self.TRAVEL_COSTS['zone_30']
        else:
            return self.TRAVEL_COSTS['zone_60']
    
    def calculate_surcharges(self, package_type: str) -> List[Tuple[str, Decimal]]:
        """Berechnet ZuschlÃ¤ge basierend auf Konfiguration"""
        surcharges = []
        
        # TT-Netz Zuschlag
        if self.site.grid_type == 'TT':
            surcharges.append(('TT-Netz Zuschlag', self.SURCHARGES['netzform_tt']))
        
        # Selektive Vorsicherung bei hoher Hauptsicherung
        if self.site.main_fuse_ampere > 35:
            surcharges.append(('Selektive Vorsicherung', self.SURCHARGES['selective_fuse']))
        
        # Kabelweg-Zuschlag (vereinfacht)
        if self.precheck.desired_power_kw > 5:  # Annahme: GrÃ¶Ãere Anlagen = lÃ¤ngere Kabelwege
            extra_meters = 10  # Beispiel: 10m extra
            surcharge = extra_meters * self.SURCHARGES['cable_length_extra']
            surcharges.append((f'Kabelweg {extra_meters}m extra', surcharge))
        
        return surcharges
    
    def calculate_discounts(self, package_type: str) -> List[Tuple[str, Decimal]]:
        """Berechnet Rabatte"""
        discounts = []
        
        # Komplett-Kit Rabatt
        if not self.precheck.own_components:
            discount_amount = self.PACKAGES[package_type]['base_price'] * self.DISCOUNTS['complete_kit']
            discounts.append(('Komplett-Kit Rabatt (15%)', discount_amount))
        
        return discounts
    
    def get_material_components(self, package_type: str) -> List[Dict]:
        """Gibt benÃ¶tigte Materialkomponenten zurÃ¼ck"""
        components = []
        
        # Basis-Komponenten
        components.extend([
            {
                'name': f'Wechselrichter {self.precheck.inverter_class}',
                'type': 'inverter',
                'quantity': 1,
                'unit_price': self._get_component_price('inverter', self.precheck.inverter_class)
            },
            {
                'name': 'AC-Verkabelung und Anschluss',
                'type': 'cable',
                'quantity': 1, 
                'unit_price': Decimal('180.00')
            }
        ])
        
        # Plus/Pro Komponenten
        if package_type in ['plus', 'pro']:
            components.extend([
                {
                    'name': 'Ãberspannungsschutz AC',
                    'type': 'spd',
                    'quantity': 1,
                    'unit_price': Decimal('320.00')
                },
                {
                    'name': 'ZÃ¤hlerplatz-ErtÃ¼chtigung',
                    'type': 'meter',
                    'quantity': 1,
                    'unit_price': Decimal('450.00')
                }
            ])
        
        # Pro Komponenten
        if package_type == 'pro' and self.precheck.storage_kwh:
            storage_price = self._get_storage_price(self.precheck.storage_kwh)
            components.append({
                'name': f'Speichersystem {self.precheck.storage_kwh} kWh',
                'type': 'battery',
                'quantity': 1,
                'unit_price': storage_price
            })
        
        return components
    
    def _get_component_price(self, component_type: str, spec: str) -> Decimal:
        """Gibt Komponentenpreis aus Datenbank oder Fallback zurÃ¼ck"""
        try:
            # Versuche Komponente aus DB zu holen
            component = Component.objects.filter(
                type=component_type
            ).first()
            if component:
                return component.unit_price
        except:
            pass
            
        # Fallback-Preise
        fallback_prices = {
            'inverter': {
                '1kva': Decimal('800.00'),
                '3kva': Decimal('1200.00'), 
                '5kva': Decimal('1800.00'),
                '10kva': Decimal('2800.00')
            }
        }
        
        return fallback_prices.get(component_type, {}).get(spec, Decimal('500.00'))
    
    def _get_storage_price(self, kwh: Decimal) -> Decimal:
        """Berechnet Speicherpreis basierend auf KapazitÃ¤t"""
        # Vereinfachte Preisberechnung: â¬800 pro kWh
        return kwh * Decimal('800.00')
    
    def calculate_quote(self) -> Quote:
        """Hauptmethode: Erstellt vollstÃ¤ndiges Angebot"""
        # Paket bestimmen
        package_type = self.determine_package()
        package = self.PACKAGES[package_type]
        
        # Quote erstellen
        quote = Quote.objects.create(
            precheck=self.precheck,
            created_by_id=1,  # TODO: Aktueller Benutzer
            status='draft'
        )
        
        # Arbeitskosten (Basis-Paket)
        QuoteItem.objects.create(
            quote=quote,
            text=f'Paket {package["name"]} - {package["description"]}',
            quantity=1,
            unit_price=package['base_price']
        )
        
        # Anfahrtskosten
        travel_cost = self.calculate_travel_cost()
        if travel_cost > 0:
            QuoteItem.objects.create(
                quote=quote,
                text='Anfahrtskosten',
                quantity=1,
                unit_price=travel_cost
            )
        
        # ZuschlÃ¤ge
        surcharges = self.calculate_surcharges(package_type)
        for name, amount in surcharges:
            QuoteItem.objects.create(
                quote=quote,
                text=name,
                quantity=1,
                unit_price=amount
            )
        
        # Materialkosten (falls EDGARD liefert)
        if not self.precheck.own_components:
            components = self.get_material_components(package_type)
            for comp in components:
                QuoteItem.objects.create(
                    quote=quote,
                    text=comp['name'],
                    quantity=comp['quantity'],
                    unit_price=comp['unit_price']
                )
        
        # Rabatte als negative Posten
        discounts = self.calculate_discounts(package_type)
        for name, amount in discounts:
            QuoteItem.objects.create(
                quote=quote,
                text=name,
                quantity=1,
                unit_price=-amount  # Negative fÃ¼r Rabatt
            )
        
        # Zwischensumme berechnen
        quote.subtotal = sum(item.line_total for item in quote.items.all())
        
        # GÃ¼ltigkeit setzen (30 Tage)
        quote.valid_until = timezone.now().date() + timedelta(days=30)
        
        # Status auf Review setzen fÃ¼r manuelle Freigabe
        quote.status = 'review'
        quote.save()
        
        return quote


# Hilfsfunktionen

def _package_label(package_key: str) -> str:
    return {
        'basis': 'Basis-Paket',
        'plus': 'Plus-Paket',
        'pro': 'Pro-Paket',
    }.get(package_key, package_key.title())


def _add_item(quote: Quote, text: str, amount: Decimal):
    if not amount or amount == Decimal('0.00'):
        return
    QuoteItem.objects.create(
        quote=quote,
        text=text,
        quantity=1,
        unit_price=amount
    )


def _build_quote_from_pricing(precheck: Precheck, pricing: Dict[str, Decimal]) -> Quote:
    quote = Quote.objects.create(
        precheck=precheck,
        created_by_id=1,
        status='review'
    )

    _add_item(quote, _package_label(pricing['package']), pricing['base_price'])
    _add_item(quote, 'Anfahrtskosten', pricing['travel_cost'])
    _add_item(quote, 'Zuschläge', pricing['surcharges'])
    _add_item(quote, 'Installation & Komponenten Wechselrichter', pricing['inverter_cost'])
    _add_item(quote, 'Speicherinstallation', pricing['storage_cost'])
    _add_item(quote, 'Wallbox & Installation', pricing['wallbox_cost'])
    _add_item(quote, 'Rabatt', -pricing['discount'])

    quote.subtotal = pricing['net_total']
    quote.vat_rate = Decimal('19.00')
    quote.vat_amount = pricing['vat_amount']
    quote.total = pricing['gross_total']
    quote.valid_until = timezone.now().date() + timedelta(days=30)
    quote.save()
    return quote


def create_quote_from_precheck(precheck_id: int):
    """Erstellt Angebot aus Vorprüfung und liefert Quote samt Preisdaten"""
    try:
        precheck = Precheck.objects.get(id=precheck_id)
        pricing_input = pricing_input_from_precheck(precheck)
        pricing = calculate_pricing(pricing_input)
        quote = _build_quote_from_pricing(precheck, pricing)
        return quote, pricing
    except Precheck.DoesNotExist:
        raise ValueError(f"Vorprüfung mit ID {precheck_id} nicht gefunden")


def recalculate_quote(quote_id: int):
    """Berechnet bestehendes Angebot neu"""
    try:
        quote = Quote.objects.get(id=quote_id)
        quote.items.all().delete()
        pricing_input = pricing_input_from_precheck(quote.precheck)
        pricing = calculate_pricing(pricing_input)
        updated_quote = _build_quote_from_pricing(quote.precheck, pricing)
        return updated_quote, pricing
    except Quote.DoesNotExist:
        raise ValueError(f"Angebot mit ID {quote_id} nicht gefunden")
