from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.customers.models import Site
from apps.core.models import User
from .validators import validate_media_file
from .helpers import inverter_label_from_power


class Component(models.Model):
    """Komponenten-Katalog"""
    COMPONENT_TYPES = [
        ('inverter', 'Wechselrichter'),
        ('battery', 'Speicher'),
        ('spd', 'Überspannungsschutz'),
        ('meter', 'Zählerplatz'),
        ('cable', 'Kabel'),
        ('switch', 'Schalter'),
        ('other', 'Sonstiges'),
    ]
    
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    vendor = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, unique=True)
    datasheet_url = models.URLField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    compatible_with = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['type', 'vendor', 'name']

    def __str__(self):
        return f"{self.vendor} {self.name}"


class Precheck(models.Model):
    """Vorprüfung"""
    WALLBOX_CLASSES = [
        ('4kw', 'Wallbox bis 4 kW'),
        ('11kw', 'Wallbox 11 kW'),
        ('22kw', 'Wallbox 22 kW'),
    ]
    WALLBOX_MOUNT_TYPES = [
        ('wall', 'Wandmontage'),
        ('stand', 'Ständermontage'),
    ]
    BUILDING_TYPE_CHOICES = [
        ('efh', 'Einfamilienhaus'),
        ('mfh', 'Mehrfamilienhaus'),
        ('commercial', 'Gewerbe'),
    ]
    GROUNDING_CHOICES = [
        ('yes', 'Ja, vorhanden'),
        ('no', 'Nein'),
        ('unknown', 'Unbekannt'),
    ]
    FEED_IN_MODE_CHOICES = [
        ('surplus', 'Überschusseinspeisung'),
        ('full', 'Volleinspeisung'),
        ('mixed', 'Gemischt'),
    ]
    INVERTER_LOCATION_CHOICES = [
        ('basement', 'Keller'),
        ('garage', 'Garage'),
        ('attic', 'Dachboden'),
        ('utility_room', 'Hauswirtschaftsraum'),
        ('outdoor', 'Außenbereich (wettergeschützt)'),
        ('other', 'Anderer Ort'),
    ]
    STORAGE_LOCATION_CHOICES = [
        ('same_as_inverter', 'Gleicher Ort wie Wechselrichter'),
        ('basement', 'Keller'),
        ('garage', 'Garage'),
        ('attic', 'Dachboden'),
        ('utility_room', 'Hauswirtschaftsraum'),
        ('outdoor', 'Außenbereich (wettergeschützt)'),
        ('other', 'Anderer Ort'),
    ]

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    # === GEBÄUDE & BAUZUSTAND ===
    building_type = models.CharField(
        max_length=20,
        choices=BUILDING_TYPE_CHOICES,
        blank=True,
        default='',
        help_text="Gebäudetyp"
    )
    construction_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Baujahr des Gebäudes"
    )
    has_renovation = models.BooleanField(
        default=False,
        help_text="Wurde eine elektrische Sanierung durchgeführt?"
    )
    renovation_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Jahr der letzten elektrischen Sanierung"
    )

    # === ELEKTRISCHE INSTALLATION ===
    has_sls_switch = models.BooleanField(
        default=False,
        help_text="SLS-Schalter (Selektiver Hauptleitungsschutzschalter) vorhanden?"
    )
    sls_switch_details = models.TextField(
        blank=True,
        default='',
        help_text="Details zum SLS-Schalter"
    )
    has_surge_protection_ac = models.BooleanField(
        default=False,
        help_text="Überspannungsschutz AC-Seite vorhanden?"
    )
    surge_protection_ac_details = models.TextField(
        blank=True,
        default='',
        help_text="Details zum AC-Überspannungsschutz"
    )
    has_surge_protection_dc = models.BooleanField(
        default=False,
        help_text="Überspannungsschutz DC-Seite gewünscht?"
    )
    has_grounding = models.CharField(
        max_length=10,
        choices=GROUNDING_CHOICES,
        blank=True,
        default='',
        help_text="Erdung/Potentialausgleich vorhanden?"
    )
    has_deep_earth = models.CharField(
        max_length=10,
        choices=GROUNDING_CHOICES,
        blank=True,
        default='',
        help_text="Tiefenerder vorhanden?"
    )
    grounding_details = models.TextField(
        blank=True,
        default='',
        help_text="Details zu Erdung/Potentialausgleich"
    )

    # === MONTAGEORTE & KABELWEGE ===
    inverter_location = models.CharField(
        max_length=50,
        choices=INVERTER_LOCATION_CHOICES,
        blank=True,
        default='',
        help_text="Montageort für Wechselrichter"
    )
    storage_location = models.CharField(
        max_length=50,
        choices=STORAGE_LOCATION_CHOICES,
        blank=True,
        default='',
        help_text="Montageort für Speicher"
    )
    distance_meter_to_inverter = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Entfernung Zählerplatz → Wechselrichter in Metern"
    )
    grid_operator = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Netzbetreiber"
    )
    # === PV-SYSTEM & KOMPONENTEN ===
    desired_power_kw = models.DecimalField(max_digits=5, decimal_places=2)
    storage_kwh = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feed_in_mode = models.CharField(
        max_length=20,
        choices=FEED_IN_MODE_CHOICES,
        blank=True,
        default='',
        help_text="Einspeise-Modus"
    )
    requires_backup_power = models.BooleanField(
        default=False,
        help_text="Inselbetr ieb/Notstrom gewünscht?"
    )
    backup_power_details = models.TextField(
        blank=True,
        default='',
        help_text="Details zu Notstrom/Inselbetrieb"
    )
    own_components = models.BooleanField(default=False, help_text="Kunde bringt eigene Komponenten mit")
    own_material_description = models.TextField(
        blank=True,
        default='',
        help_text="Beschreibung der eigenen Komponenten"
    )

    # === ZUSATZGERÄTE ===
    has_heat_pump = models.BooleanField(
        default=False,
        help_text="Wärmepumpe vorhanden?"
    )
    heat_pump_cascade = models.BooleanField(
        default=False,
        help_text="Kaskadenschaltung für Wärmepumpe gewünscht?"
    )
    heat_pump_details = models.TextField(
        blank=True,
        default='',
        help_text="Details zur Wärmepumpe"
    )
    wallbox = models.BooleanField(default=False, help_text="Kunde wünscht eine Wallbox")
    wallbox_class = models.CharField(
        max_length=4,
        choices=WALLBOX_CLASSES,
        blank=True,
        default='',
        help_text="Gewünschte Wallbox-Leistungsklasse"
    )
    wallbox_mount = models.CharField(
        max_length=10,
        choices=WALLBOX_MOUNT_TYPES,
        blank=True,
        default='',
        help_text="Montageart der Wallbox"
    )
    wallbox_cable_prepared = models.BooleanField(
        default=False,
        help_text="Ist die Zuleitung bereits vorbereitet?"
    )
    wallbox_cable_length_m = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Länge der Wallbox-Zuleitung in Metern"
    )

    PACKAGE_CHOICES = [
        ('', 'Kein Paket ausgewählt'),
        ('basis', 'Basis-Paket'),
        ('plus', 'Plus-Paket'),
        ('pro', 'Pro-Paket'),
    ]

    package_choice = models.CharField(
        max_length=10,
        choices=PACKAGE_CHOICES,
        blank=True,
        default='',
        help_text="Vom Kunden gewünschtes Leistungspaket"
    )
    is_express_package = models.BooleanField(
        default=False,
        help_text="Express-Paket ohne technische Precheck-Details"
    )
    wallbox_pv_surplus = models.BooleanField(
        default=False,
        help_text="PV-Überschussladen für die Wallbox gewünscht"
    )

    # FILE UPLOADS - Fotos für technische Bewertung
    meter_cabinet_photo = models.FileField(
        upload_to='precheck/meter_cabinet/%Y/%m/',
        validators=[validate_media_file],
        null=True,
        blank=True,
        help_text="Datei Zählerschrank (JPG, PNG oder PDF, max 5MB)"
    )
    hak_photo = models.FileField(
        upload_to='precheck/hak/%Y/%m/',
        validators=[validate_media_file],
        null=True,
        blank=True,
        help_text="Datei Hausanschlusskasten (JPG, PNG oder PDF, max 5MB)"
    )
    location_photo = models.FileField(
        upload_to='precheck/locations/%Y/%m/',
        validators=[validate_media_file],
        null=True,
        blank=True,
        help_text="Datei Montageorte (JPG, PNG oder PDF, max 5MB)"
    )
    cable_route_photo = models.FileField(
        upload_to='precheck/cables/%Y/%m/',
        validators=[validate_media_file],
        null=True,
        blank=True,
        help_text="Datei Kabelwege (JPG, PNG oder PDF, max 5MB)"
    )

    # Legacy-Feld (behalten für Rückwärtskompatibilität)
    component_files = models.TextField(default='[]', help_text="JSON Liste der hochgeladenen Komponentendatenblätter")

    # Terminwunsch
    preferred_timeframes = models.TextField(default='[]', help_text="JSON Gewünschte Zeitfenster")

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Vorprüfung {self.site.customer.name} - {self.desired_power_kw} kW"

    @property
    def inverter_label(self) -> str:
        return inverter_label_from_power(self.desired_power_kw or Decimal('0'))

    def get_all_uploads(self):
        """Helper-Methode: Gibt alle hochgeladenen Dateien zurück"""
        files = []
        photo_categories = set()

        # Primär alle Dateien aus PrecheckPhoto (Mehrfach-Uploads)
        for photo in self.photos.all():
            files.append((photo.get_category_display(), photo.photo))
            photo_categories.add(photo.category)

        # Legacy-Felder nur ergänzen, wenn keine PrecheckPhoto-Einträge existieren
        legacy_mapping = [
            ('meter_cabinet', 'Zählerschrank', self.meter_cabinet_photo),
            ('hak', 'Hausanschlusskasten', self.hak_photo),
            ('location', 'Montageorte', self.location_photo),
            ('cable_route', 'Kabelwege', self.cable_route_photo),
        ]

        for category, label, file_field in legacy_mapping:
            if file_field and category not in photo_categories:
                files.append((label, file_field))

        return files


class PrecheckPhoto(models.Model):
    """Mehrere Fotos pro Kategorie für Precheck"""
    CATEGORY_CHOICES = [
        ('meter_cabinet', 'Zählerschrank'),
        ('hak', 'Hausanschlusskasten'),
        ('location', 'Montageorte'),
        ('cable_route', 'Kabelwege'),
    ]

    precheck = models.ForeignKey(Precheck, on_delete=models.CASCADE, related_name='photos')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    photo = models.FileField(
        upload_to='precheck/photos/%Y/%m/',
        validators=[validate_media_file],
        help_text="Datei (JPG, PNG oder PDF, max 5MB)"
    )
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['category', 'uploaded_at']
        verbose_name = 'Precheck Foto'
        verbose_name_plural = 'Precheck Fotos'

    def __str__(self):
        return f"{self.get_category_display()} - {self.precheck.id}"


class Quote(models.Model):
    """Angebot"""
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('review', 'In Prüfung'),
        ('approved', 'Freigegeben'),
        ('sent', 'Versendet'),
        ('accepted', 'Angenommen'),
        ('rejected', 'Abgelehnt'),
        ('expired', 'Abgelaufen'),
    ]
    
    precheck = models.OneToOneField(Precheck, on_delete=models.CASCADE)
    quote_number = models.CharField(max_length=20, unique=True)
    
    # Preise
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'))
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    pdf_url = models.URLField(blank=True)
    
    # Metadaten
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quotes')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_quotes')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    valid_until = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Angebot {self.quote_number}"

    def save(self, *args, **kwargs):
        if not self.quote_number:
            # Generiere Angebotsnummer
            year = timezone.now().year
            count = Quote.objects.filter(created_at__year=year).count() + 1
            self.quote_number = f"PV-{year}-{count:04d}"
        
        # Berechne Totalsumme
        self.vat_amount = self.subtotal * (self.vat_rate / 100)
        self.total = self.subtotal + self.vat_amount
        
        super().save(*args, **kwargs)


class QuoteItem(models.Model):
    """Angebots-Position"""
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(Component, on_delete=models.CASCADE, null=True, blank=True)
    
    # Überschreibbare Felder
    text = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.text} - {self.quantity} x {self.unit_price}€"


class ProductCategory(models.Model):
    """
    Produktkategorien für den Artikelkatalog
    z.B. Installationsmaterial, Kabel, Dienstleistungen, Wechselrichter, Speicher, Zubehör
    """
    name = models.CharField(max_length=200, unique=True, verbose_name="Kategoriename")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    sort_order = models.IntegerField(default=0, verbose_name="Sortierreihenfolge")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Produktkategorie'
        verbose_name_plural = 'Produktkategorien'

    def __str__(self):
        return self.name

    def get_product_count(self):
        """Anzahl der Produkte in dieser Kategorie"""
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    """
    Artikelkatalog für Produkte und Dienstleistungen
    Verwendet für Angebotserstellung und Precheck-Kalkulation
    """
    UNIT_CHOICES = [
        ('piece', 'Stück'),
        ('meter', 'Meter'),
        ('hour', 'Stunde'),
        ('kwh', 'kWh'),
        ('kwp', 'kWp'),
        ('set', 'Set'),
        ('package', 'Paket'),
        ('lump_sum', 'Pauschal'),
        ('percent', 'Prozent'),
    ]

    VAT_RATE_CHOICES = [
        (Decimal('0.00'), '0% (Steuerfrei)'),
        (Decimal('0.07'), '7% (Ermäßigt)'),
        (Decimal('0.19'), '19% (Standard)'),
    ]

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name="Kategorie"
    )

    # Grunddaten
    name = models.CharField(max_length=200, verbose_name="Bezeichnung")
    sku = models.CharField(max_length=100, unique=True, verbose_name="Artikelnummer")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece', verbose_name="Einheit")

    # Preise
    purchase_price_net = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Einkaufspreis (netto)"
    )
    sales_price_net = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Verkaufspreis (netto)"
    )
    vat_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        choices=VAT_RATE_CHOICES,
        default=Decimal('0.19'),
        verbose_name="MwSt.-Satz"
    )

    # Lagerbestand (optional)
    stock_quantity = models.IntegerField(default=0, blank=True, null=True, verbose_name="Lagerbestand")
    min_stock_level = models.IntegerField(default=0, blank=True, null=True, verbose_name="Mindestbestand")

    # Status
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    is_featured = models.BooleanField(default=False, verbose_name="Hervorgehoben")

    # Zusatzinformationen
    manufacturer = models.CharField(max_length=200, blank=True, verbose_name="Hersteller")
    supplier = models.CharField(max_length=200, blank=True, verbose_name="Lieferant")
    notes = models.TextField(blank=True, verbose_name="Notizen")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        ordering = ['category__sort_order', 'category__name', 'name']
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def sales_price_gross(self):
        """Verkaufspreis brutto (berechnet)"""
        return self.sales_price_net * (1 + self.vat_rate)

    @property
    def purchase_price_gross(self):
        """Einkaufspreis brutto (berechnet)"""
        return self.purchase_price_net * (1 + self.vat_rate)

    @property
    def margin_amount(self):
        """Marge in Euro"""
        return self.sales_price_net - self.purchase_price_net

    @property
    def margin_percentage(self):
        """Marge in Prozent"""
        if self.purchase_price_net > 0:
            return ((self.sales_price_net - self.purchase_price_net) / self.purchase_price_net) * 100
        return Decimal('0.00')

    @property
    def is_low_stock(self):
        """Prüft, ob Lagerbestand unter Mindestbestand liegt"""
        if self.stock_quantity is not None and self.min_stock_level is not None:
            return self.stock_quantity <= self.min_stock_level
        return False

    def get_unit_display_short(self):
        """Kurze Einheit-Anzeige"""
        unit_map = {
            'piece': 'Stk.',
            'meter': 'm',
            'hour': 'h',
            'kwh': 'kWh',
            'kwp': 'kWp',
            'set': 'Set',
            'package': 'Pkt.',
            'lump_sum': 'Psch.',
            'percent': '%',
        }
        return unit_map.get(self.unit, self.get_unit_display())
