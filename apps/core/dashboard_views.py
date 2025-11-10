"""
Dashboard Views für EDGARD PV-Service
Class-Based Views für das Admin-Dashboard

Alle Views erfordern Login (LoginRequiredMixin)
Optimierte Queries mit select_related/prefetch_related
"""
import csv
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, Sum, Q, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    TemplateView,
    ListView,
    DeleteView,
    DetailView,
    UpdateView,
    View
)

from apps.customers.models import Customer, Site
from apps.quotes.models import Precheck, Quote, PriceConfig, QuoteItem
from .forms import PriceConfigForm


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """
    Dashboard Startseite mit Statistiken und Übersichten

    Zeigt:
    - Anzahl Prechecks (gesamt, diese Woche, heute)
    - Anzahl Angebote (nach Status)
    - Anzahl Kunden (gesamt, neu diese Woche)
    - Letzte Aktivitäten
    """
    template_name = 'dashboard/home.html'
    login_url = '/admin/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Zeitfenster für Statistiken
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)

        # Precheck Statistiken
        prechecks_total = Precheck.objects.count()
        prechecks_week = Precheck.objects.filter(created_at__gte=week_start).count()
        prechecks_today = Precheck.objects.filter(created_at__gte=today_start).count()

        # Quote Statistiken nach Status
        quotes_stats = Quote.objects.values('status').annotate(
            count=Count('id'),
            total_value=Sum('total')
        ).order_by('status')

        # Customer Statistiken
        customers_total = Customer.objects.count()
        customers_week = Customer.objects.filter(created_at__gte=week_start).count()

        # Letzte Prechecks (optimiert mit select_related)
        recent_prechecks = Precheck.objects.select_related(
            'site__customer'
        ).order_by('-created_at')[:10]

        # Letzte Angebote (optimiert mit select_related)
        recent_quotes = Quote.objects.select_related(
            'precheck__site__customer',
            'created_by'
        ).order_by('-created_at')[:10]

        # Angebote die bald ablaufen (nächste 7 Tage)
        expiring_soon = Quote.objects.filter(
            status__in=['sent', 'review'],
            valid_until__lte=now.date() + timedelta(days=7),
            valid_until__gte=now.date()
        ).select_related(
            'precheck__site__customer'
        ).order_by('valid_until')

        context.update({
            'prechecks_total': prechecks_total,
            'prechecks_week': prechecks_week,
            'prechecks_today': prechecks_today,
            'quotes_stats': quotes_stats,
            'customers_total': customers_total,
            'customers_week': customers_week,
            'recent_prechecks': recent_prechecks,
            'recent_quotes': recent_quotes,
            'expiring_soon': expiring_soon,
        })

        return context


class PrecheckListView(LoginRequiredMixin, ListView):
    """
    Liste aller Prechecks mit Such- und Filterfunktion

    Features:
    - Suche nach Kunde, Adresse
    - Filter nach Leistung, Speicher, Wallbox
    - Paginierung (25 pro Seite)
    - Optimierte Queries
    """
    model = Precheck
    template_name = 'dashboard/precheck_list.html'
    context_object_name = 'prechecks'
    paginate_by = 25
    login_url = '/admin/login/'

    def get_queryset(self):
        """
        Optimierte Queryset mit Suche und Filterung
        """
        queryset = Precheck.objects.select_related(
            'site__customer'
        ).order_by('-created_at')

        # Suchfunktion
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(site__customer__name__icontains=search_query) |
                Q(site__customer__email__icontains=search_query) |
                Q(site__address__icontains=search_query) |
                Q(notes__icontains=search_query)
            )

        # Filter: Wallbox
        has_wallbox = self.request.GET.get('wallbox')
        if has_wallbox:
            queryset = queryset.filter(wallbox=True)

        # Filter: Speicher
        has_storage = self.request.GET.get('storage')
        if has_storage:
            queryset = queryset.filter(storage_kwh__isnull=False, storage_kwh__gt=0)

        # Filter: Leistungsbereich
        power_min = self.request.GET.get('power_min')
        power_max = self.request.GET.get('power_max')
        if power_min:
            try:
                queryset = queryset.filter(desired_power_kw__gte=Decimal(power_min))
            except (ValueError, TypeError):
                pass
        if power_max:
            try:
                queryset = queryset.filter(desired_power_kw__lte=Decimal(power_max))
            except (ValueError, TypeError):
                pass

        # Filter: Eigene Komponenten
        own_components = self.request.GET.get('own_components')
        if own_components:
            queryset = queryset.filter(own_components=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Suchparameter für Template
        context['search_query'] = self.request.GET.get('search', '')
        context['filter_wallbox'] = self.request.GET.get('wallbox', '')
        context['filter_storage'] = self.request.GET.get('storage', '')
        context['filter_power_min'] = self.request.GET.get('power_min', '')
        context['filter_power_max'] = self.request.GET.get('power_max', '')
        context['filter_own_components'] = self.request.GET.get('own_components', '')

        return context


class PrecheckDetailView(LoginRequiredMixin, DetailView):
    """
    Detailansicht eines Prechecks

    Zeigt alle Informationen inkl.:
    - Kundendaten
    - Standortdaten
    - Technische Details
    - Hochgeladene Fotos
    - Zugehöriges Angebot (falls vorhanden)
    """
    model = Precheck
    template_name = 'dashboard/precheck_detail.html'
    context_object_name = 'precheck'
    login_url = '/admin/login/'

    def get_queryset(self):
        """
        Optimierte Query mit allen benötigten Relations
        """
        return Precheck.objects.select_related(
            'site__customer'
        ).prefetch_related(
            Prefetch(
                'quote',
                queryset=Quote.objects.select_related('created_by', 'approved_by')
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Alle hochgeladenen Dateien
        context['uploaded_files'] = self.object.get_all_uploads()

        # Zugehöriges Angebot
        try:
            context['quote'] = self.object.quote
        except Quote.DoesNotExist:
            context['quote'] = None

        return context


class PrecheckExportView(LoginRequiredMixin, View):
    """
    CSV-Export aller Prechecks

    Exportiert alle sichtbaren Prechecks basierend auf aktuellen Filtern
    CSV-Format mit allen relevanten Feldern
    """
    login_url = '/admin/login/'

    def get(self, request, *args, **kwargs):
        """
        Generiert CSV-Datei mit Precheck-Daten
        """
        # Erstelle Response mit CSV-Header
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="prechecks_export_{timestamp}.csv"'

        # UTF-8 BOM für Excel-Kompatibilität
        response.write('\ufeff')

        # CSV Writer erstellen
        writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)

        # Header-Zeile
        writer.writerow([
            'ID',
            'Erstellt am',
            'Kunde',
            'Kunde E-Mail',
            'Kunde Telefon',
            'Kundentyp',
            'Standort Adresse',
            'Gebäudetyp',
            'Baujahr',
            'Hauptsicherung (A)',
            'Netztyp',
            'Gewünschte Leistung (kW)',
            'Speicher (kWh)',
            'Eigene Komponenten',
            'Wallbox gewünscht',
            'Wallbox Leistung',
            'Wallbox Montage',
            'Wallbox Kabel vorbereitet',
            'Wallbox Kabellänge (m)',
            'Entfernung Zähler-HAK (m)',
            'Fotos vorhanden',
            'Notizen',
        ])

        # Daten-Zeilen (mit optimierter Query)
        prechecks = Precheck.objects.select_related(
            'site__customer'
        ).order_by('-created_at')

        for precheck in prechecks:
            site = precheck.site
            customer = site.customer

            # Fotos zählen
            photos = []
            if precheck.meter_cabinet_photo:
                photos.append('Zählerschrank')
            if precheck.hak_photo:
                photos.append('HAK')
            if precheck.location_photo:
                photos.append('Montageort')
            if precheck.cable_route_photo:
                photos.append('Kabelweg')
            photos_str = ', '.join(photos) if photos else 'Keine'

            writer.writerow([
                precheck.id,
                precheck.created_at.strftime('%d.%m.%Y %H:%M'),
                customer.name,
                customer.email,
                customer.phone,
                customer.get_customer_type_display(),
                site.address,
                site.get_building_type_display(),
                site.construction_year or '',
                site.main_fuse_ampere,
                site.get_grid_type_display(),
                str(precheck.desired_power_kw),
                str(precheck.storage_kwh) if precheck.storage_kwh else '',
                'Ja' if precheck.own_components else 'Nein',
                'Ja' if precheck.wallbox else 'Nein',
                precheck.get_wallbox_class_display() if precheck.wallbox_class else '',
                precheck.get_wallbox_mount_display() if precheck.wallbox_mount else '',
                'Ja' if precheck.wallbox_cable_prepared else 'Nein',
                str(precheck.wallbox_cable_length_m) if precheck.wallbox_cable_length_m else '',
                str(site.distance_meter_to_hak),
                photos_str,
                precheck.notes,
            ])

        return response


class PriceConfigListView(LoginRequiredMixin, ListView):
    """
    Liste aller Preiskonfigurationen

    Gruppiert nach Kategorien:
    - Anfahrt & Zonen
    - Zuschläge
    - Pakete
    - Material
    - Wallbox
    - Kabel
    """
    model = PriceConfig
    template_name = 'dashboard/price_list.html'
    context_object_name = 'prices'
    login_url = '/admin/login/'

    def get_queryset(self):
        """
        Alle Preiskonfigurationen sortiert nach Typ
        """
        return PriceConfig.objects.all().order_by('price_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Gruppiere Preise nach Kategorien
        prices = self.get_queryset()

        grouped_prices = {
            'Anfahrt & Zonen': [],
            'Zuschläge': [],
            'Pakete': [],
            'Material': [],
            'Wallbox': [],
            'Kabel': [],
        }

        for price in prices:
            price_type = price.price_type

            if price_type.startswith('travel_'):
                grouped_prices['Anfahrt & Zonen'].append(price)
            elif price_type.startswith('surcharge_') or price_type.startswith('discount_'):
                grouped_prices['Zuschläge'].append(price)
            elif price_type.startswith('package_'):
                grouped_prices['Pakete'].append(price)
            elif price_type.startswith('material_'):
                grouped_prices['Material'].append(price)
            elif price_type.startswith('wallbox_'):
                grouped_prices['Wallbox'].append(price)
            elif price_type.startswith('cable_'):
                grouped_prices['Kabel'].append(price)

        context['grouped_prices'] = grouped_prices

        return context


class PriceConfigUpdateView(LoginRequiredMixin, UpdateView):
    """
    Bearbeiten einer Preiskonfiguration

    Erlaubt Änderung von:
    - Wert (value)
    - Beschreibung

    Typ kann nicht geändert werden (unique constraint)
    """
    model = PriceConfig
    form_class = PriceConfigForm
    template_name = 'dashboard/price_update.html'
    context_object_name = 'price'
    success_url = reverse_lazy('dashboard:price_list')
    login_url = '/admin/login/'

    def form_valid(self, form):
        """
        Bei erfolgreicher Validierung: Success-Message
        """
        messages.success(
            self.request,
            f'Preiskonfiguration "{self.object.get_price_type_display()}" wurde aktualisiert.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Bei Validierungsfehlern: Error-Message
        """
        messages.error(
            self.request,
            'Fehler beim Speichern der Preiskonfiguration. Bitte prüfen Sie Ihre Eingaben.'
        )
        return super().form_invalid(form)


class CustomerListView(LoginRequiredMixin, ListView):
    """
    Liste aller Kunden mit Suchfunktion

    Features:
    - Suche nach Name, E-Mail, Telefon
    - Filter nach Kundentyp
    - Anzahl Standorte und Prechecks pro Kunde
    - Paginierung (25 pro Seite)
    """
    model = Customer
    template_name = 'dashboard/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 25
    login_url = '/admin/login/'

    def get_queryset(self):
        """
        Optimierte Query mit Aggregation
        """
        queryset = Customer.objects.annotate(
            sites_count=Count('sites', distinct=True),
            prechecks_count=Count('sites__precheck', distinct=True)
        ).order_by('-created_at')

        # Suchfunktion
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(address__icontains=search_query)
            )

        # Filter: Kundentyp
        customer_type = self.request.GET.get('type')
        if customer_type and customer_type in ['private', 'business']:
            queryset = queryset.filter(customer_type=customer_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Suchparameter für Template
        context['search_query'] = self.request.GET.get('search', '')
        context['filter_type'] = self.request.GET.get('type', '')

        # Statistiken
        context['total_count'] = Customer.objects.count()
        context['private_count'] = Customer.objects.filter(customer_type='private').count()
        context['business_count'] = Customer.objects.filter(customer_type='business').count()

        return context


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """
    Detailansicht eines Kunden

    Zeigt:
    - Kundenstammdaten
    - Alle Standorte
    - Alle Prechecks
    - Alle Angebote
    - DSGVO-Consent-Informationen
    """
    model = Customer
    template_name = 'dashboard/customer_detail.html'
    context_object_name = 'customer'
    login_url = '/admin/login/'

    def get_queryset(self):
        """
        Optimierte Query mit allen Relations
        """
        return Customer.objects.prefetch_related(
            Prefetch(
                'sites',
                queryset=Site.objects.prefetch_related(
                    Prefetch(
                        'precheck_set',
                        queryset=Precheck.objects.select_related('quote')
                    )
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Alle Standorte mit Prechecks
        sites = self.object.sites.all()
        context['sites'] = sites

        # Alle Prechecks über alle Standorte
        all_prechecks = Precheck.objects.filter(
            site__customer=self.object
        ).select_related('site').order_by('-created_at')
        context['prechecks'] = all_prechecks

        # Alle Angebote über Prechecks
        all_quotes = Quote.objects.filter(
            precheck__site__customer=self.object
        ).select_related(
            'precheck__site',
            'created_by'
        ).order_by('-created_at')
        context['quotes'] = all_quotes

        return context


class QuoteListView(LoginRequiredMixin, ListView):
    """
    Liste aller Angebote mit Such- und Filterfunktion

    Features:
    - Suche nach Angebotsnummer, Kunde
    - Filter nach Status
    - Sortierung nach Datum, Wert
    - Paginierung (25 pro Seite)
    """
    model = Quote
    template_name = 'dashboard/quote_list.html'
    context_object_name = 'quotes'
    paginate_by = 25
    login_url = '/admin/login/'

    def get_queryset(self):
        """
        Optimierte Query mit Suche und Filterung
        """
        queryset = Quote.objects.select_related(
            'precheck__site__customer',
            'created_by',
            'approved_by'
        ).order_by('-created_at')

        # Suchfunktion
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(quote_number__icontains=search_query) |
                Q(precheck__site__customer__name__icontains=search_query) |
                Q(precheck__site__customer__email__icontains=search_query)
            )

        # Filter: Status
        status = self.request.GET.get('status')
        if status and status in dict(Quote.STATUS_CHOICES):
            queryset = queryset.filter(status=status)

        # Sortierung
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['created_at', '-created_at', 'total', '-total', 'quote_number', '-quote_number']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Suchparameter für Template
        context['search_query'] = self.request.GET.get('search', '')
        context['filter_status'] = self.request.GET.get('status', '')
        context['sort_by'] = self.request.GET.get('sort', '-created_at')

        # Status-Choices für Filter-Dropdown
        context['status_choices'] = Quote.STATUS_CHOICES

        # Statistiken pro Status
        status_stats = Quote.objects.values('status').annotate(
            count=Count('id'),
            total_value=Sum('total')
        )
        context['status_stats'] = {stat['status']: stat for stat in status_stats}

        return context


class QuoteDetailView(LoginRequiredMixin, DetailView):
    """
    Detailansicht eines Angebots

    Zeigt:
    - Angebotsdaten
    - Kundendaten
    - Precheck-Daten
    - Alle Positionen (QuoteItems)
    - Preisberechnung
    - Statushistorie
    """
    model = Quote
    template_name = 'dashboard/quote_detail.html'
    context_object_name = 'quote'
    login_url = '/admin/login/'

    def get_queryset(self):
        """
        Optimierte Query mit allen Relations
        """
        return Quote.objects.select_related(
            'precheck__site__customer',
            'created_by',
            'approved_by'
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=QuoteItem.objects.select_related('component').order_by('id')
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Alle Positionen
        context['items'] = self.object.items.all()

        # Kunde und Precheck
        context['customer'] = self.object.precheck.site.customer
        context['precheck'] = self.object.precheck
        context['site'] = self.object.precheck.site

        return context


# =============================================================================
# DELETE VIEWS - Löschfunktionen
# =============================================================================

class PrecheckDeleteView(LoginRequiredMixin, DeleteView):
    """
    Löschen eines Prechecks

    WICHTIG: Löscht CASCADE:
    - Verknüpfte Quotes und QuoteItems
    - Hochgeladene Dateien (meter_cabinet_photo, hak_photo, etc.)

    ACHTUNG: Löscht NICHT den Customer/Site!
    Die bleiben erhalten für andere Prechecks.
    """
    model = Precheck
    login_url = '/admin/login/'
    success_url = reverse_lazy('dashboard:precheck_list')

    def delete(self, request, *args, **kwargs):
        """
        Überschreibt delete() um eine Success-Message anzuzeigen
        """
        precheck = self.get_object()
        precheck_id = precheck.id
        customer_name = precheck.site.customer.name

        # Lösche das Objekt
        response = super().delete(request, *args, **kwargs)

        # Success-Message
        messages.success(
            request,
            f'Precheck #{precheck_id} von {customer_name} wurde erfolgreich gelöscht.'
        )

        return response


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    """
    Löschen eines Kunden

    WICHTIG: Löscht CASCADE:
    - Alle Sites des Kunden
    - Alle Prechecks aller Sites
    - Alle Quotes aller Prechecks
    - Alle hochgeladenen Dateien

    WARNUNG: Dies ist eine destruktive Operation!
    Alle Daten des Kunden gehen unwiderruflich verloren.
    """
    model = Customer
    login_url = '/admin/login/'
    success_url = reverse_lazy('dashboard:customer_list')

    def delete(self, request, *args, **kwargs):
        """
        Überschreibt delete() um eine Success-Message anzuzeigen
        und Statistiken zu sammeln
        """
        customer = self.get_object()
        customer_name = customer.name
        customer_id = customer.id

        # Sammle Statistiken vor dem Löschen
        sites_count = customer.sites.count()
        prechecks_count = Precheck.objects.filter(site__customer=customer).count()
        quotes_count = Quote.objects.filter(precheck__site__customer=customer).count()

        # Lösche das Objekt (CASCADE löscht alles verknüpfte)
        response = super().delete(request, *args, **kwargs)

        # Success-Message mit Statistiken
        messages.success(
            request,
            f'Kunde "{customer_name}" (ID #{customer_id}) wurde gelöscht. '
            f'Entfernt: {sites_count} Standorte, {prechecks_count} Prechecks, {quotes_count} Angebote.'
        )

        return response
