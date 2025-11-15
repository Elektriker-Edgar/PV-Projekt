from django import forms
from django.utils import timezone
from apps.customers.models import Customer, Site
from .models import Precheck, PrecheckPhoto


FILE_CATEGORY_MAP = {
    'meter_cabinet_photo': 'meter_cabinet',
    'hak_photo': 'hak',
    'location_photo': 'location',
    'cable_route_photo': 'cable_route',
}


def _get_primary_file(cleaned_data, uploaded_files, field_name):
    """
    Pick the first uploaded file per Feld für die Legacy-Felder auf Site/Precheck.
    """
    uploaded_files = uploaded_files or {}
    files = uploaded_files.get(field_name)
    if files:
        return files[0]
    return cleaned_data.get(field_name)


def _create_precheck_photos(precheck, uploaded_files):
    """
    Speichert alle hochgeladenen Dateien in PrecheckPhoto für Mehrfach-Uploads.
    """
    if not uploaded_files:
        return

    for field_name, category in FILE_CATEGORY_MAP.items():
        for file in uploaded_files.get(field_name, []) or []:
            PrecheckPhoto.objects.create(
                precheck=precheck,
                category=category,
                photo=file
            )


class PrecheckForm(forms.Form):
    """Vereinfachtes Precheck-Formular"""
    
    # Kundendaten
    customer_name = forms.CharField(
        max_length=200, 
        label="Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Max Mustermann'})
    )
    customer_email = forms.EmailField(
        label="E-Mail",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'max@example.com'})
    )
    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Telefon",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+49 40 12345678'})
    )
    customer_type = forms.ChoiceField(
        choices=Customer.CUSTOMER_TYPES,
        label="Kundentyp",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        initial='private'
    )
    customer_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Straße, PLZ Ort'})
    )
    # === GEBÄUDE & BAUZUSTAND ===
    building_type = forms.ChoiceField(
        choices=[('', 'Bitte wählen...')] + list(Precheck.BUILDING_TYPE_CHOICES),
        label="Gebäudetyp",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    construction_year = forms.IntegerField(
        required=False,
        label="Baujahr",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1990'})
    )
    has_renovation = forms.BooleanField(
        required=False,
        label="Letzte Sanierung durchgeführt",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    renovation_year = forms.IntegerField(
        required=False,
        label="Jahr der letzten Sanierung",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2020'})
    )

    # === ELEKTRISCHE INSTALLATION ===
    main_fuse_ampere = forms.IntegerField(
        label="Hauptsicherung (A)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '63'})
    )
    grid_type = forms.ChoiceField(
        choices=Site.GRID_TYPES,
        label="Hausanschluss (optional)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    has_sls_switch = forms.BooleanField(
        required=False,
        label="SLS-Schalter vorhanden",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    sls_switch_details = forms.CharField(
        required=False,
        label="Details zum SLS-Schalter",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    has_surge_protection_ac = forms.BooleanField(
        required=False,
        label="Überspannungsschutz AC vorhanden",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    surge_protection_ac_details = forms.CharField(
        required=False,
        label="Details zum Überspannungsschutz AC",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    has_grounding = forms.ChoiceField(
        required=False,
        choices=[('', 'Bitte wählen...')] + list(Precheck.GROUNDING_CHOICES),
        label="Erdung/Potentialausgleich",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    has_deep_earth = forms.ChoiceField(
        required=False,
        choices=[('', 'Bitte wählen...')] + list(Precheck.GROUNDING_CHOICES),
        label="Tiefenerder",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    grounding_details = forms.CharField(
        required=False,
        label="Details zu Erdung/Potentialausgleich",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    # === MONTAGEORTE & KABELWEGE ===
    inverter_location = forms.ChoiceField(
        required=True,
        label="Montageort Wechselrichter",
        choices=[('', 'Wählen Sie...')] + list(Precheck.INVERTER_LOCATION_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    storage_location = forms.ChoiceField(
        required=False,
        label="Montageort Speicher",
        choices=[('', 'Kein Speicher geplant')] + list(Precheck.STORAGE_LOCATION_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    distance_meter_to_inverter = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=True,
        label="Entfernung Zählerplatz → Wechselrichter (m)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '5.0'})
    )
    grid_operator = forms.CharField(
        required=False,
        label="Netzbetreiber",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Dateien (Fotos/PDFs)
    meter_cabinet_photo = forms.FileField(
        required=False,
        label="Datei Zählerschrank",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,application/pdf'})
    )
    hak_photo = forms.FileField(
        required=False,
        label="Datei Hausanschlusskasten",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,application/pdf'})
    )
    location_photo = forms.FileField(
        required=False,
        label="Datei Montageorte",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,application/pdf'})
    )
    cable_route_photo = forms.FileField(
        required=False,
        label="Datei Kabelwege",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,application/pdf'})
    )
    
    # === PV-SYSTEM & KOMPONENTEN ===
    desired_power_kw = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Gewünschte WR-Leistung (kW)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '3.0'})
    )
    storage_kwh = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label="Gewünschte Speicherkapazität (kWh)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '10.0'})
    )
    feed_in_mode = forms.ChoiceField(
        required=False,
        choices=[('', 'Bitte wählen...')] + list(Precheck.FEED_IN_MODE_CHOICES),
        label="Einspeise-Modus",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    requires_backup_power = forms.BooleanField(
        required=False,
        label="Inselbetrieb/Notstrom gewünscht",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    backup_power_details = forms.CharField(
        required=False,
        label="Details zu Notstrom/Inselbetrieb",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    has_surge_protection_dc = forms.BooleanField(
        required=False,
        label="Überspannungsschutz DC-Seite gewünscht",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    own_components = forms.BooleanField(
        required=False,
        label="Ich bringe eigene Komponenten mit",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    own_material_description = forms.CharField(
        required=False,
        label="Beschreibung eigener Komponenten",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    has_wallbox = forms.BooleanField(
        required=False,
        label="Wallbox gewünscht",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    wallbox_power = forms.ChoiceField(
        required=False,
        choices=Precheck.WALLBOX_CLASSES,
        label="Wallbox Leistungsklasse",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    wallbox_mount = forms.ChoiceField(
        required=False,
        choices=Precheck.WALLBOX_MOUNT_TYPES,
        label="Montage-Art",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    wallbox_pv_surplus = forms.BooleanField(
        required=False,
        label="PV-Überschussladen aktivieren",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    wallbox_cable_installed = forms.BooleanField(
        required=False,
        label="Kabel bereits verlegt",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    wallbox_cable_length = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        min_value=0,
        label="Kabellänge Zählerplatz zu Wallbox (m)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '10'})
    )

    # === WÄRMEPUMPE ===
    has_heat_pump = forms.BooleanField(
        required=False,
        label="Wärmepumpe vorhanden",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    heat_pump_cascade = forms.BooleanField(
        required=False,
        label="Kaskadenschaltung für Wärmepumpe gewünscht",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    heat_pump_details = forms.CharField(
        required=False,
        label="Details zur Wärmepumpe",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    notes = forms.CharField(
        required=False,
        label="Anmerkungen",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Besondere Wünsche oder Anmerkungen...'})
    )
    
    # DSGVO
    consent = forms.BooleanField(
        label="Ich stimme der Verarbeitung meiner Daten zu",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned = super().clean()
        if cleaned.get('has_wallbox'):
            if not cleaned.get('wallbox_power'):
                self.add_error('wallbox_power', "Bitte wählen Sie eine Wallbox-Leistungsklasse.")
            if not cleaned.get('wallbox_mount'):
                self.add_error('wallbox_mount', "Bitte wählen Sie die Wallbox-Montageart.")
            if not cleaned.get('wallbox_cable_installed') and not cleaned.get('wallbox_cable_length'):
                self.add_error('wallbox_cable_length', "Bitte geben Sie die Kabellänge an oder markieren Sie, dass sie bereits verlegt ist.")
        return cleaned

    def save(self, uploaded_files=None):
        """Erstelle Customer, Site und Precheck aus Formulardaten"""
        # IP-Adresse würde normalerweise aus request.META['REMOTE_ADDR'] kommen
        consent_ip = '127.0.0.1'  # Placeholder
        uploaded_files = uploaded_files or {}
        primary_files = {
            field: _get_primary_file(self.cleaned_data, uploaded_files, field)
            for field in FILE_CATEGORY_MAP.keys()
        }
        
        # Customer erstellen
        customer_type = self.cleaned_data.get('customer_type') or Customer.CUSTOMER_TYPES[0][0]
        customer = Customer.objects.create(
            name=self.cleaned_data['customer_name'],
            email=self.cleaned_data['customer_email'],
            phone=self.cleaned_data.get('customer_phone', ''),
            customer_type=customer_type,
            address=self.cleaned_data.get('customer_address', ''),
            consent_timestamp=timezone.now(),
            consent_ip=consent_ip
        )
        
        # Site erstellen
        # Legacy-Feld distance_meter_to_hak wird mit distance_meter_to_inverter befüllt
        distance_value = self.cleaned_data.get('distance_meter_to_inverter') or 0

        site = Site.objects.create(
            customer=customer,
            address=self.cleaned_data.get('customer_address', ''),
            building_type=self.cleaned_data.get('building_type', ''),
            construction_year=self.cleaned_data.get('construction_year'),
            main_fuse_ampere=self.cleaned_data['main_fuse_ampere'],
            grid_type=self.cleaned_data.get('grid_type') or '',
            distance_meter_to_hak=distance_value,
            meter_cabinet_photo=primary_files['meter_cabinet_photo'],
            hak_photo=primary_files['hak_photo']
        )
        
        has_wallbox = self.cleaned_data.get('has_wallbox', False)
        wallbox_cable_length = self.cleaned_data.get('wallbox_cable_length')
        wallbox_pv_surplus = self.cleaned_data.get('wallbox_pv_surplus', False)
        if not has_wallbox:
            wallbox_power = ''
            wallbox_mount = ''
            wallbox_cable_prepared = False
            wallbox_cable_length = None
            wallbox_pv_surplus = False
        else:
            wallbox_power = self.cleaned_data.get('wallbox_power') or ''
            wallbox_mount = self.cleaned_data.get('wallbox_mount') or ''
            wallbox_cable_prepared = self.cleaned_data.get('wallbox_cable_installed', False)
            if wallbox_cable_prepared:
                wallbox_cable_length = None

        # Precheck erstellen mit File-Uploads
        precheck = Precheck.objects.create(
            site=site,
            # Gebäude & Bauzustand
            building_type=self.cleaned_data.get('building_type') or '',
            construction_year=self.cleaned_data.get('construction_year'),
            has_renovation=self.cleaned_data.get('has_renovation', False),
            renovation_year=self.cleaned_data.get('renovation_year'),
            # Elektrische Installation
            has_sls_switch=self.cleaned_data.get('has_sls_switch', False),
            sls_switch_details=self.cleaned_data.get('sls_switch_details', ''),
            has_surge_protection_ac=self.cleaned_data.get('has_surge_protection_ac', False),
            surge_protection_ac_details=self.cleaned_data.get('surge_protection_ac_details', ''),
            has_grounding=self.cleaned_data.get('has_grounding', ''),
            has_deep_earth=self.cleaned_data.get('has_deep_earth', ''),
            grounding_details=self.cleaned_data.get('grounding_details', ''),
            # Montageorte & Kabelwege
            inverter_location=self.cleaned_data.get('inverter_location', ''),
            storage_location=self.cleaned_data.get('storage_location', ''),
            distance_meter_to_inverter=self.cleaned_data.get('distance_meter_to_inverter'),
            grid_operator=self.cleaned_data.get('grid_operator', ''),
            # PV-System
            desired_power_kw=self.cleaned_data['desired_power_kw'],
            storage_kwh=self.cleaned_data.get('storage_kwh'),
            feed_in_mode=self.cleaned_data.get('feed_in_mode', ''),
            requires_backup_power=self.cleaned_data.get('requires_backup_power', False),
            backup_power_details=self.cleaned_data.get('backup_power_details', ''),
            has_surge_protection_dc=self.cleaned_data.get('has_surge_protection_dc', False),
            own_components=self.cleaned_data.get('own_components', False),
            own_material_description=self.cleaned_data.get('own_material_description', ''),
            # Wallbox
            wallbox=has_wallbox,
            wallbox_class=wallbox_power,
            wallbox_mount=wallbox_mount,
            wallbox_cable_prepared=wallbox_cable_prepared,
            wallbox_cable_length_m=wallbox_cable_length,
            wallbox_pv_surplus=wallbox_pv_surplus,
            # Wärmepumpe
            has_heat_pump=self.cleaned_data.get('has_heat_pump', False),
            heat_pump_cascade=self.cleaned_data.get('heat_pump_cascade', False),
            heat_pump_details=self.cleaned_data.get('heat_pump_details', ''),
            # Notizen
            notes=self.cleaned_data.get('notes', ''),
            # File Uploads
            meter_cabinet_photo=primary_files['meter_cabinet_photo'],
            hak_photo=primary_files['hak_photo'],
            location_photo=primary_files['location_photo'],
            cable_route_photo=primary_files['cable_route_photo']
        )

        _create_precheck_photos(precheck, uploaded_files)
        return precheck


class ExpressPackageForm(forms.Form):
    """Vereinfachtes Express-Paket-Formular (ohne technische Details)"""

    # Kundendaten (gleich wie Precheck)
    customer_name = forms.CharField(
        max_length=200,
        label="Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Max Mustermann'})
    )
    customer_email = forms.EmailField(
        label="E-Mail",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'max@example.com'})
    )
    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Telefon (optional)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+49 40 12345678'})
    )
    customer_address = forms.CharField(
        label="Installationsadresse",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Straße, PLZ Ort'})
    )
    building_type = forms.ChoiceField(
        choices=Site._meta.get_field('building_type').choices,
        label="Gebäudetyp",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Dateien (gleich wie Precheck)
    meter_cabinet_photo = forms.FileField(
        required=False,
        label="Datei Zählerschrank (optional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,application/pdf'})
    )
    hak_photo = forms.FileField(
        required=False,
        label="Datei Hausanschlusskasten (optional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,application/pdf'})
    )
    location_photo = forms.FileField(
        required=False,
        label="Datei Montageorte (optional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,application/pdf'})
    )
    cable_route_photo = forms.FileField(
        required=False,
        label="Datei Kabelwege (optional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,application/pdf'})
    )

    # Besonderheiten/Kundenwünsche
    special_requests = forms.CharField(
        required=False,
        label="Besonderheiten / Kundenwünsche",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Besondere Wünsche, Anmerkungen, oder technische Details...'
        })
    )

    # DSGVO
    consent = forms.BooleanField(
        label="Ich stimme der Verarbeitung meiner Daten zu",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def save(self, package_choice, uploaded_files=None):
        """Erstelle Customer, Site und Precheck aus Formulardaten (Express-Paket)"""
        consent_ip = '127.0.0.1'  # Placeholder
        uploaded_files = uploaded_files or {}
        primary_files = {
            field: _get_primary_file(self.cleaned_data, uploaded_files, field)
            for field in FILE_CATEGORY_MAP.keys()
        }

        # Customer erstellen
        customer = Customer.objects.create(
            name=self.cleaned_data['customer_name'],
            email=self.cleaned_data['customer_email'],
            phone=self.cleaned_data.get('customer_phone', ''),
            customer_type='private',  # Express-Pakete nur für Privatkunden
            address=self.cleaned_data['customer_address'],
            consent_timestamp=timezone.now(),
            consent_ip=consent_ip
        )

        # Site erstellen (mit Minimal-Daten)
        site = Site.objects.create(
            customer=customer,
            address=self.cleaned_data['customer_address'],
            building_type=self.cleaned_data['building_type'],
            construction_year=None,  # Nicht relevant für Express-Pakete
            main_fuse_ampere=35,  # Default-Wert
            grid_type='',
            distance_meter_to_hak=0,  # Default-Wert
        )

        # Precheck erstellen (als Express-Paket)
        precheck = Precheck.objects.create(
            site=site,
            desired_power_kw=0,  # Wird später von Techniker festgelegt
            storage_kwh=None,
            own_components=False,
            wallbox=False,
            package_choice=package_choice,
            is_express_package=True,  # Markierung als Express-Paket
            notes=self.cleaned_data.get('special_requests', ''),
            # File Uploads
            meter_cabinet_photo=primary_files['meter_cabinet_photo'],
            hak_photo=primary_files['hak_photo'],
            location_photo=primary_files['location_photo'],
            cable_route_photo=primary_files['cable_route_photo']
        )

        _create_precheck_photos(precheck, uploaded_files)
        return precheck





