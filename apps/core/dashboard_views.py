"""
Dashboard Views für EDGARD PV-Service
Class-Based Views für das Admin-Dashboard

Alle Views erfordern Login (LoginRequiredMixin)
Optimierte Queries mit select_related/prefetch_related
"""
import csv
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import urlencode
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, Sum, Q, Prefetch
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
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
from apps.quotes.models import Precheck, Quote, QuoteItem, ProductCategory, Product
from .forms import ProductCategoryForm, ProductForm, QuoteEditForm, QuoteItemFormSet
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


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
        ).prefetch_related('photos').order_by('-created_at')

        for precheck in prechecks:
            site = precheck.site
            customer = site.customer

            # Fotos zählen
            photo_labels = {
                'meter_cabinet': 'Zählerschrank',
                'hak': 'HAK',
                'location': 'Montageort',
                'cable_route': 'Kabelweg',
            }
            photo_categories = set()

            legacy_files = {
                'meter_cabinet': precheck.meter_cabinet_photo,
                'hak': precheck.hak_photo,
                'location': precheck.location_photo,
                'cable_route': precheck.cable_route_photo,
            }
            for category, value in legacy_files.items():
                if value:
                    photo_categories.add(category)

            for photo in precheck.photos.all():
                photo_categories.add(photo.category)

            photos = [
                label for key, label in photo_labels.items()
                if key in photo_categories
            ]
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


class PrecheckPDFExportView(LoginRequiredMixin, View):
    """
    PDF-Export eines einzelnen Prechecks

    Generiert professionelle PDF mit allen erfassten Daten
    Verwendet ReportLab für PDF-Generierung
    """
    login_url = '/admin/login/'

    def get(self, request, pk, *args, **kwargs):
        """
        Generiert PDF-Datei für einen Precheck
        """
        # Precheck mit allen Relations laden
        precheck = get_object_or_404(
            Precheck.objects.select_related(
                'site__customer'
            ).prefetch_related(
                Prefetch(
                    'quote',
                    queryset=Quote.objects.select_related('created_by', 'approved_by')
                )
            ),
            pk=pk
        )

        # Alle hochgeladenen Dateien
        uploaded_files = precheck.get_all_uploads()

        # Zugehöriges Angebot
        try:
            quote = precheck.quote
        except Quote.DoesNotExist:
            quote = None

        # Response mit PDF
        response = HttpResponse(content_type='application/pdf')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = ''.join(c if c.isalnum() or c in (' ', '_') else '_' for c in precheck.site.customer.name[:30])
        filename = f'Precheck_{precheck.id}_{safe_name}_{timestamp}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # PDF erstellen
        doc = SimpleDocTemplate(response, pagesize=A4,
                                rightMargin=20*mm, leftMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)

        # Styles
        styles = getSampleStyleSheet()
        story = []

        # Custom Styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=8,
            spaceBefore=12,
            borderWidth=0,
            borderPadding=6,
            backColor=colors.HexColor('#dbeafe'),
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
        )

        # Header
        story.append(Paragraph(f'Precheck #{precheck.id}', title_style))
        story.append(Paragraph(
            f'Erstellt am {precheck.created_at.strftime("%d.%m.%Y, %H:%M")} Uhr | '
            f'Exportiert am {datetime.now().strftime("%d.%m.%Y, %H:%M")} Uhr',
            normal_style
        ))
        story.append(Spacer(1, 12))

        # Helper function für Daten-Tabellen
        def add_data_table(heading, data_rows):
            if not data_rows:
                return
            story.append(Paragraph(heading, heading_style))
            t = Table(data_rows, colWidths=[80*mm, 90*mm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

        # Kundendaten
        customer_data = [
            ['Name:', Paragraph(precheck.site.customer.name, normal_style)],
            ['E-Mail:', Paragraph(precheck.site.customer.email, normal_style)],
            ['Telefon:', Paragraph(precheck.site.customer.phone or '–', normal_style)],
            ['Kundentyp:', Paragraph(precheck.site.customer.get_customer_type_display(), normal_style)],
        ]
        add_data_table('👤 Kundendaten', customer_data)

        # Gebäude & Bauzustand
        building_data = [
            ['Adresse:', Paragraph(precheck.site.address.replace('\n', '<br/>'), normal_style)],
        ]
        if precheck.building_type:
            building_data.append(['Gebäudetyp:', Paragraph(precheck.get_building_type_display(), normal_style)])
        if precheck.construction_year:
            building_data.append(['Baujahr:', Paragraph(str(precheck.construction_year), normal_style)])

        renovation_text = 'Ja'
        if precheck.renovation_year:
            renovation_text += f' ({precheck.renovation_year})'
        building_data.append(['Elektr. Sanierung:', Paragraph(
            renovation_text if precheck.has_renovation else 'Nein', normal_style
        )])
        add_data_table('🏢 Gebäude & Bauzustand', building_data)

        # Elektrische Installation
        electrical_data = [
            ['Hauptsicherung:', Paragraph(f'<b>{precheck.site.main_fuse_ampere} A</b>', normal_style)],
        ]
        if precheck.site.grid_type:
            electrical_data.append(['Netztyp:', Paragraph(precheck.site.get_grid_type_display(), normal_style)])

        electrical_data.append(['SLS-Schalter:', Paragraph('Ja' if precheck.has_sls_switch else 'Nein', normal_style)])
        if precheck.sls_switch_details:
            electrical_data.append(['SLS Details:', Paragraph(precheck.sls_switch_details, normal_style)])

        electrical_data.append(['Überspannungsschutz AC:', Paragraph('Vorhanden' if precheck.has_surge_protection_ac else 'Nicht vorhanden', normal_style)])
        if precheck.surge_protection_ac_details:
            electrical_data.append(['ÜS AC Details:', Paragraph(precheck.surge_protection_ac_details, normal_style)])

        electrical_data.append(['Überspannungsschutz DC:', Paragraph('Gewünscht' if precheck.has_surge_protection_dc else 'Nicht gewünscht', normal_style)])

        if precheck.has_grounding:
            grounding_map = {'yes': 'Ja, vorhanden', 'no': 'Nein', 'unknown': 'Unbekannt'}
            electrical_data.append(['Erdung:', Paragraph(grounding_map.get(precheck.has_grounding, '–'), normal_style)])

        if precheck.has_deep_earth:
            deep_earth_map = {'yes': 'Ja, vorhanden', 'no': 'Nein', 'unknown': 'Unbekannt'}
            electrical_data.append(['Tiefenerder:', Paragraph(deep_earth_map.get(precheck.has_deep_earth, '–'), normal_style)])

        if precheck.grounding_details:
            electrical_data.append(['Erdung Details:', Paragraph(precheck.grounding_details, normal_style)])

        add_data_table('⚡ Elektrische Installation', electrical_data)

        # Montageorte & Kabelwege
        location_data = []
        if precheck.inverter_location:
            location_data.append(['WR-Standort:', Paragraph(precheck.inverter_location, normal_style)])
        if precheck.storage_location:
            location_data.append(['Speicher-Standort:', Paragraph(precheck.storage_location, normal_style)])

        location_data.append(['Entfernung Zähler → HAK:', Paragraph(f'{precheck.site.distance_meter_to_hak} m', normal_style)])

        if precheck.distance_meter_to_inverter:
            location_data.append(['Entfernung Zähler → WR:', Paragraph(f'{precheck.distance_meter_to_inverter} m', normal_style)])

        if precheck.grid_operator:
            location_data.append(['Netzbetreiber:', Paragraph(precheck.grid_operator, normal_style)])

        if location_data:
            add_data_table('📍 Montageorte & Kabelwege', location_data)

        # PV-System & Komponenten
        pv_data = [
            ['Gewünschte Leistung:', Paragraph(f'<b>{precheck.desired_power_kw} kW</b>', normal_style)],
            ['WR-Klasse:', Paragraph(precheck.inverter_label, normal_style)],
            ['Speicher:', Paragraph(f'{precheck.storage_kwh} kWh' if precheck.storage_kwh else 'Kein Speicher', normal_style)],
        ]

        if precheck.feed_in_mode:
            pv_data.append(['Einspeise-Modus:', Paragraph(precheck.get_feed_in_mode_display(), normal_style)])

        pv_data.append(['Notstrom:', Paragraph('Gewünscht' if precheck.requires_backup_power else 'Nicht gewünscht', normal_style)])
        if precheck.backup_power_details:
            pv_data.append(['Notstrom Details:', Paragraph(precheck.backup_power_details, normal_style)])

        pv_data.append(['Eigene Komponenten:', Paragraph('Ja' if precheck.own_components else 'Nein', normal_style)])
        if precheck.own_material_description:
            pv_data.append(['Eigene Komp. Details:', Paragraph(precheck.own_material_description, normal_style)])

        add_data_table('☀️ PV-System & Komponenten', pv_data)

        # Wallbox
        if precheck.wallbox:
            wallbox_data = [
                ['Wallbox-Klasse:', Paragraph(precheck.get_wallbox_class_display(), normal_style)],
            ]
            if precheck.wallbox_mount:
                wallbox_data.append(['Montageart:', Paragraph(precheck.get_wallbox_mount_display(), normal_style)])

            wallbox_data.append(['PV-Überschussladen:', Paragraph('Ja' if precheck.wallbox_pv_surplus else 'Nein', normal_style)])
            wallbox_data.append(['Zuleitung vorbereitet:', Paragraph('Ja' if precheck.wallbox_cable_prepared else 'Nein', normal_style)])

            if precheck.wallbox_cable_length_m:
                wallbox_data.append(['Kabellänge:', Paragraph(f'{precheck.wallbox_cable_length_m} m', normal_style)])

            add_data_table('🔌 Wallbox-Konfiguration', wallbox_data)

        # Wärmepumpe
        if precheck.has_heat_pump:
            hp_data = [
                ['Wärmepumpe vorhanden:', Paragraph('Ja', normal_style)],
                ['Kaskadenschaltung:', Paragraph('Gewünscht' if precheck.heat_pump_cascade else 'Nicht gewünscht', normal_style)],
            ]
            if precheck.heat_pump_details:
                hp_data.append(['WP Details:', Paragraph(precheck.heat_pump_details, normal_style)])

            add_data_table('🔥 Wärmepumpe', hp_data)

        # Hochgeladene Fotos
        if uploaded_files:
            story.append(Paragraph('📷 Hochgeladene Fotos', heading_style))
            photo_list = '<br/>'.join([f'• {label}' for label, _ in uploaded_files])
            story.append(Paragraph(photo_list, normal_style))
            story.append(Spacer(1, 8))

        # Anmerkungen
        if precheck.notes:
            story.append(Paragraph('📝 Anmerkungen', heading_style))
            story.append(Paragraph(precheck.notes.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 8))

        # Zugehöriges Angebot
        if quote:
            story.append(PageBreak())
            quote_data = [
                ['Angebots-Nr.:', Paragraph(f'<b>{quote.quote_number}</b>', normal_style)],
                ['Status:', Paragraph(quote.get_status_display(), normal_style)],
                ['Erstellt am:', Paragraph(quote.created_at.strftime('%d.%m.%Y, %H:%M') + ' Uhr', normal_style)],
            ]
            if quote.valid_until:
                quote_data.append(['Gültig bis:', Paragraph(quote.valid_until.strftime('%d.%m.%Y'), normal_style)])

            quote_data.append(['Gesamtpreis (brutto):', Paragraph(f'<b>{quote.total:.2f} €</b>', normal_style)])
            add_data_table('📄 Zugehöriges Angebot', quote_data)

        # PDF bauen
        doc.build(story)

        return response


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


class CustomerBulkDeleteView(LoginRequiredMixin, View):
    """
    Mehrfachlöschung von Kunden

    WICHTIG: Löscht CASCADE für jeden Kunden:
    - Alle Sites des Kunden
    - Alle Prechecks aller Sites
    - Alle Quotes aller Prechecks
    - Alle hochgeladenen Dateien

    WARNUNG: Dies ist eine destruktive Operation!
    """
    login_url = '/admin/login/'

    def post(self, request, *args, **kwargs):
        """
        Verarbeitet die Mehrfachlöschung
        """
        # Extrahiere Kunden-IDs aus POST-Parameter
        customer_ids_str = request.POST.get('customer_ids', '')

        if not customer_ids_str:
            messages.error(request, 'Keine Kunden ausgewählt.')
            return redirect('dashboard:customer_list')

        # Konvertiere String zu Liste von Integer-IDs
        try:
            customer_ids = [int(id.strip()) for id in customer_ids_str.split(',') if id.strip()]
        except ValueError:
            messages.error(request, 'Ungültige Kunden-IDs.')
            return redirect('dashboard:customer_list')

        if not customer_ids:
            messages.error(request, 'Keine Kunden ausgewählt.')
            return redirect('dashboard:customer_list')

        # Hole alle Kunden
        customers = Customer.objects.filter(id__in=customer_ids)

        if not customers.exists():
            messages.error(request, 'Keine gültigen Kunden gefunden.')
            return redirect('dashboard:customer_list')

        # Sammle Statistiken vor dem Löschen
        total_customers = customers.count()
        total_sites = 0
        total_prechecks = 0
        total_quotes = 0
        customer_names = []

        for customer in customers:
            customer_names.append(customer.name)
            total_sites += customer.sites.count()
            total_prechecks += Precheck.objects.filter(site__customer=customer).count()
            total_quotes += Quote.objects.filter(precheck__site__customer=customer).count()

        # Lösche alle Kunden (CASCADE löscht alles verknüpfte)
        customers.delete()

        # Success-Message mit Statistiken
        messages.success(
            request,
            f'{total_customers} Kunden wurden gelöscht. '
            f'Entfernt: {total_sites} Standorte, {total_prechecks} Prechecks, {total_quotes} Angebote.'
        )

        return redirect('dashboard:customer_list')


class QuoteBulkDeleteView(LoginRequiredMixin, View):
    """
    Mehrfachlöschung von Angeboten

    WICHTIG: Löscht CASCADE:
    - Alle QuoteItems des Angebots
    - Alle verknüpften Dateien

    WARNUNG: Dies ist eine destruktive Operation!
    """
    login_url = '/admin/login/'

    def post(self, request, *args, **kwargs):
        """
        Verarbeitet die Mehrfachlöschung von Angeboten
        """
        # Extrahiere Angebots-IDs aus POST-Parameter
        quote_ids_str = request.POST.get('quote_ids', '')

        if not quote_ids_str:
            messages.error(request, 'Keine Angebote ausgewählt.')
            return redirect('dashboard:quote_list')

        # Konvertiere String zu Liste von Integer-IDs
        try:
            quote_ids = [int(id.strip()) for id in quote_ids_str.split(',') if id.strip()]
        except ValueError:
            messages.error(request, 'Ungültige Angebots-IDs.')
            return redirect('dashboard:quote_list')

        if not quote_ids:
            messages.error(request, 'Keine Angebote ausgewählt.')
            return redirect('dashboard:quote_list')

        # Hole alle Angebote
        quotes = Quote.objects.filter(id__in=quote_ids)

        if not quotes.exists():
            messages.error(request, 'Keine gültigen Angebote gefunden.')
            return redirect('dashboard:quote_list')

        # Sammle Statistiken vor dem Löschen
        total_quotes = quotes.count()
        total_value = sum(quote.total_gross for quote in quotes)
        quote_numbers = [quote.quote_number for quote in quotes]

        # Lösche alle Angebote (CASCADE löscht alle QuoteItems)
        quotes.delete()

        # Success-Message mit Statistiken
        messages.success(
            request,
            f'{total_quotes} Angebote wurden gelöscht. Gesamtwert: {total_value:.2f} € (Brutto)'
        )

        return redirect('dashboard:quote_list')


# =============================================================================
# PRODUCT CATALOG VIEWS - Produktkatalog-System
# =============================================================================

class ProductCategoryListView(LoginRequiredMixin, ListView):
    """
    Liste aller Produktkategorien

    Features:
    - Zeigt alle Kategorien mit Produktanzahl
    - Sortierung nach sort_order
    - Aktiv/Inaktiv Status
    - Inline-Aktionen
    """
    model = ProductCategory
    template_name = 'dashboard/category_list.html'
    context_object_name = 'categories'
    login_url = '/admin/login/'

    def get_queryset(self):
        """
        Optimierte Query mit Produktanzahl
        """
        queryset = ProductCategory.objects.annotate(
            active_product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('sort_order', 'name')

        # Suchfunktion
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['total_categories'] = ProductCategory.objects.count()
        context['active_categories'] = ProductCategory.objects.filter(is_active=True).count()
        return context


class ProductCategoryCreateView(LoginRequiredMixin, View):
    """
    Erstellen einer neuen Produktkategorie (AJAX)
    """
    login_url = '/admin/login/'

    def post(self, request, *args, **kwargs):
        """
        Erstellt eine neue Kategorie und gibt JSON zurück
        """
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Kategoriename darf nicht leer sein.')
            return redirect('dashboard:category_list')

        # Prüfe ob Kategorie bereits existiert
        if ProductCategory.objects.filter(name=name).exists():
            messages.error(request, f'Kategorie "{name}" existiert bereits.')
            return redirect('dashboard:category_list')

        # Erstelle Kategorie
        try:
            # Ermittle höchste sort_order
            from django.db.models import Max
            max_sort = ProductCategory.objects.aggregate(Max('sort_order'))['sort_order__max'] or 0

            category = ProductCategory.objects.create(
                name=name,
                description=description,
                sort_order=max_sort + 10
            )
            messages.success(request, f'Kategorie "{category.name}" wurde erfolgreich erstellt.')
        except Exception as e:
            messages.error(request, f'Fehler beim Erstellen der Kategorie: {str(e)}')

        return redirect('dashboard:category_list')


class ProductCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """
    Bearbeiten einer Produktkategorie
    """
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'dashboard/category_form.html'
    context_object_name = 'category'
    success_url = reverse_lazy('dashboard:category_list')
    login_url = '/admin/login/'

    def form_valid(self, form):
        """
        Bei erfolgreicher Validierung: Success-Message
        """
        messages.success(
            self.request,
            f'Kategorie "{self.object.name}" wurde aktualisiert.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Bei Validierungsfehlern: Error-Message
        """
        messages.error(
            self.request,
            'Fehler beim Speichern der Kategorie. Bitte prüfen Sie Ihre Eingaben.'
        )
        return super().form_invalid(form)


class ProductCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """
    Löschen einer Produktkategorie

    WICHTIG: Verwendet PROTECT in models.py
    Kategorie kann nicht gelöscht werden wenn noch Produkte zugeordnet sind
    """
    model = ProductCategory
    login_url = '/admin/login/'
    success_url = reverse_lazy('dashboard:category_list')

    def delete(self, request, *args, **kwargs):
        """
        Überschreibt delete() um eine Success-Message anzuzeigen
        """
        category = self.get_object()
        category_name = category.name

        # Prüfe ob Produkte vorhanden sind
        product_count = category.products.count()
        if product_count > 0:
            messages.error(
                request,
                f'Kategorie "{category_name}" kann nicht gelöscht werden. '
                f'Es sind noch {product_count} Produkt(e) zugeordnet.'
            )
            return redirect('dashboard:category_list')

        # Lösche das Objekt
        response = super().delete(request, *args, **kwargs)

        # Success-Message
        messages.success(
            request,
            f'Kategorie "{category_name}" wurde erfolgreich gelöscht.'
        )

        return response


class ProductListView(LoginRequiredMixin, ListView):
    """
    Liste aller Produkte mit Filter und Suche

    Features:
    - Suche nach Name, SKU, Hersteller
    - Filter nach Kategorie
    - Filter nach Status (aktiv/inaktiv)
    - Sortierung nach verschiedenen Feldern
    - Paginierung (50 pro Seite)
    - Zeigt Bruttopreise
    """
    FILTER_FIELDS = ('search', 'category', 'status', 'featured', 'sort')
    FILTER_SESSION_KEY = 'product_list_filters'

    model = Product
    template_name = 'dashboard/product_list.html'
    context_object_name = 'products'
    paginate_by = 50
    login_url = '/admin/login/'

    def get(self, request, *args, **kwargs):
        reset_requested = request.GET.get('reset') == '1'
        if reset_requested:
            request.session.pop(self.FILTER_SESSION_KEY, None)
            return redirect(request.path)

        stored_filters = request.session.get(self.FILTER_SESSION_KEY, {})
        if stored_filters and not self._has_filter_query(request):
            query_string = urlencode(stored_filters)
            if query_string:
                return redirect(f"{request.path}?{query_string}")

        response = super().get(request, *args, **kwargs)
        self._persist_filters(request)
        return response

    def get_queryset(self):
        """
        Optimierte Query mit Suche und Filterung
        """
        queryset = Product.objects.select_related('category').order_by('category__sort_order', 'name')

        # Suchfunktion
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(manufacturer__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Filter: Kategorie
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                queryset = queryset.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass

        # Filter: Status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Filter: Hervorgehoben
        featured = self.request.GET.get('featured')
        if featured == 'yes':
            queryset = queryset.filter(is_featured=True)

        # Sortierung
        sort_by = self.request.GET.get('sort', 'name')
        if sort_by in ['name', '-name', 'sku', '-sku', 'sales_price_net', '-sales_price_net', 'category__name', '-category__name']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Suchparameter für Template
        context['search_query'] = self.request.GET.get('search', '')
        context['filter_category'] = self.request.GET.get('category', '')
        context['filter_status'] = self.request.GET.get('status', '')
        context['filter_featured'] = self.request.GET.get('featured', '')
        context['sort_by'] = self.request.GET.get('sort', 'name')

        # Alle Kategorien für Filter-Dropdown
        context['categories'] = ProductCategory.objects.filter(is_active=True).order_by('sort_order', 'name')

        # Statistiken
        context['total_products'] = Product.objects.count()
        context['active_products'] = Product.objects.filter(is_active=True).count()
        context['featured_products'] = Product.objects.filter(is_featured=True).count()

        return context

    def _has_filter_query(self, request):
        return any(request.GET.get(field) not in (None, '') for field in self.FILTER_FIELDS)

    def _persist_filters(self, request):
        filters = {
            field: request.GET.get(field)
            for field in self.FILTER_FIELDS
        }
        clean_filters = {k: v for k, v in filters.items() if v not in (None, '')}

        if clean_filters:
            request.session[self.FILTER_SESSION_KEY] = clean_filters
        else:
            request.session.pop(self.FILTER_SESSION_KEY, None)


class ProductBulkActionView(LoginRequiredMixin, View):
    """
    Verarbeitet Mehrfachaktionen (Löschen, Verschieben, Kopieren) für Produkte.
    """
    login_url = '/admin/login/'

    def post(self, request, *args, **kwargs):
        selected_ids = request.POST.getlist('selected_products')
        action = request.POST.get('bulk_action')

        if not selected_ids:
            messages.error(request, 'Bitte wählen Sie mindestens ein Produkt aus.')
            return redirect('dashboard:product_list')

        if action == 'delete':
            products = Product.objects.filter(id__in=selected_ids)
            count = products.count()
            names = list(products.values_list('name', flat=True))
            products.delete()
            messages.success(
                request,
                f'{count} Produkt(e) wurden gelöscht: {", ".join(names[:3])}{"..." if count > 3 else ""}'
            )
            return redirect('dashboard:product_list')

        if action == 'move':
            target_category_id = request.POST.get('target_category')
            if not target_category_id:
                messages.error(request, 'Bitte wählen Sie eine Zielkategorie für die Verschiebung aus.')
                return redirect('dashboard:product_list')
            try:
                category = ProductCategory.objects.get(id=target_category_id)
            except ProductCategory.DoesNotExist:
                messages.error(request, 'Die ausgewählte Zielkategorie existiert nicht.')
                return redirect('dashboard:product_list')

            updated = Product.objects.filter(id__in=selected_ids).update(category=category)
            messages.success(
                request,
                f'{updated} Produkt(e) wurden in die Kategorie "{category.name}" verschoben.'
            )
            return redirect('dashboard:product_list')

        if action == 'copy':
            if len(selected_ids) != 1:
                messages.error(request, 'Bitte wählen Sie genau ein Produkt zum Kopieren aus.')
                return redirect('dashboard:product_list')
            product_id = selected_ids[0]
            messages.info(request, 'Produkt wird kopiert. Bitte passen Sie die Daten im folgenden Formular an.')
            copy_url = f"{reverse('dashboard:product_create')}?copy_from={product_id}"
            return redirect(copy_url)

        messages.error(request, 'Unbekannte Aktion. Bitte wählen Sie eine gültige Massenaktion aus.')
        return redirect('dashboard:product_list')


class ProductCreateView(LoginRequiredMixin, View):
    """
    Erstellen eines neuen Produkts
    Verwendet GET für Formular-Anzeige und POST für Speichern
    """
    login_url = '/admin/login/'

    def get(self, request, *args, **kwargs):
        """
        Zeigt Formular zum Erstellen eines neuen Produkts
        """
        initial = self._get_copy_initial(request)
        form = ProductForm(initial=initial)
        return render(request, 'dashboard/product_form.html', {
            'form': form,
            'is_create': True,
        })

    def post(self, request, *args, **kwargs):
        """
        Speichert neues Produkt
        """
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Produkt "{product.name}" wurde erfolgreich erstellt.')
            return redirect('dashboard:product_list')
        else:
            messages.error(request, 'Fehler beim Erstellen des Produkts. Bitte prüfen Sie Ihre Eingaben.')
            return render(request, 'dashboard/product_form.html', {
                'form': form,
                'is_create': True,
            })

    def _get_copy_initial(self, request):
        copy_from = request.GET.get('copy_from')
        if not copy_from:
            return {}
        try:
            product = Product.objects.get(pk=copy_from)
        except Product.DoesNotExist:
            messages.error(request, 'Das ausgewählte Produkt konnte nicht gefunden werden.')
            return {}

        return {
            'category': product.category_id,
            'name': product.name,
            'sku': product.sku,
            'description': product.description,
            'unit': product.unit,
            'purchase_price_net': product.purchase_price_net,
            'sales_price_net': product.sales_price_net,
            'vat_rate': product.vat_rate,
            'stock_quantity': product.stock_quantity,
            'min_stock_level': product.min_stock_level,
            'manufacturer': product.manufacturer,
            'supplier': product.supplier,
            'notes': product.notes,
            'is_active': product.is_active,
            'is_featured': product.is_featured,
        }


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """
    Bearbeiten eines Produkts
    """
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    context_object_name = 'product'
    success_url = reverse_lazy('dashboard:product_list')
    login_url = '/admin/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False
        return context

    def form_valid(self, form):
        """
        Bei erfolgreicher Validierung: Success-Message
        """
        messages.success(
            self.request,
            f'Produkt "{self.object.name}" wurde aktualisiert.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Bei Validierungsfehlern: Error-Message
        """
        messages.error(
            self.request,
            'Fehler beim Speichern des Produkts. Bitte prüfen Sie Ihre Eingaben.'
        )
        return super().form_invalid(form)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """
    Löschen eines Produkts

    WARNUNG: Dies löscht das Produkt permanent
    Prüft ob Produkt in Angeboten verwendet wird
    """
    model = Product
    login_url = '/admin/login/'
    success_url = reverse_lazy('dashboard:product_list')

    def delete(self, request, *args, **kwargs):
        """
        Überschreibt delete() um eine Success-Message anzuzeigen
        """
        product = self.get_object()
        product_name = product.name
        product_sku = product.sku

        # Lösche das Objekt
        response = super().delete(request, *args, **kwargs)

        # Success-Message
        messages.success(
            request,
            f'Produkt "{product_name}" (SKU: {product_sku}) wurde erfolgreich gelöscht.'
        )

        return response


class QuoteEditView(LoginRequiredMixin, View):
    """
    View zum Bearbeiten von Angeboten
    
    Ermöglicht:
    - Bearbeitung von Quote-Metadaten (Status, MwSt, Notizen)
    - Bearbeitung von QuoteItems (Positionen hinzufügen/ändern/löschen)
    - Automatische Neuberechnung der Summen
    """
    login_url = '/admin/login/'
    template_name = 'dashboard/quote_edit.html'

    def get(self, request, pk):
        quote = get_object_or_404(Quote.objects.select_related('precheck__site__customer'), pk=pk)
        quote_form = QuoteEditForm(instance=quote)
        items_formset = QuoteItemFormSet(instance=quote)
        
        return render(request, self.template_name, {
            'quote': quote,
            'quote_form': quote_form,
            'items_formset': items_formset,
        })

    def post(self, request, pk):
        quote = get_object_or_404(Quote.objects.select_related('precheck__site__customer'), pk=pk)
        quote_form = QuoteEditForm(request.POST, instance=quote)
        items_formset = QuoteItemFormSet(request.POST, instance=quote)

        if quote_form.is_valid() and items_formset.is_valid():
            # Speichere Quote-Metadaten
            quote_form.save(commit=False)
            
            # Speichere QuoteItems
            items_formset.save()
            
            # Neuberechnung der Summen
            quote.subtotal = sum(item.line_total for item in quote.items.all())
            quote.save()  # Triggert automatisch vat_amount und total Berechnung
            
            messages.success(request, f'Angebot {quote.quote_number} wurde erfolgreich aktualisiert.')
            return redirect('dashboard:quote_detail', pk=quote.pk)
        else:
            # Fehlerbehandlung
            messages.error(request, 'Bitte überprüfen Sie Ihre Eingaben.')
            return render(request, self.template_name, {
                'quote': quote,
                'quote_form': quote_form,
                'items_formset': items_formset,
            })


class ProductAutocompleteView(LoginRequiredMixin, View):
    """
    JSON API für Produkt-Autocomplete
    Sucht Produkte basierend auf Name oder SKU
    """
    login_url = '/admin/login/'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        include_inactive = request.GET.get('include_inactive', 'false').lower() == 'true'

        if len(query) < 2:
            return JsonResponse({'results': []})

        # Suche nach Name, SKU oder Hersteller
        filters = Q(name__icontains=query) | Q(sku__icontains=query) | Q(manufacturer__icontains=query)

        if not include_inactive:
            filters &= Q(is_active=True)

        products = Product.objects.filter(filters).select_related('category').order_by('-is_active', 'name')[:10]

        results = []
        for product in products:
            results.append({
                'id': product.id,
                'text': product.name,
                'sku': product.sku,
                'price': float(product.sales_price_net),
                'vat_rate': float(product.vat_rate_percent),
                'unit': product.unit,
                'category': product.category.name if product.category else '',
                'manufacturer': product.manufacturer or '',
                'is_active': product.is_active,
            })

        return JsonResponse({'results': results})
