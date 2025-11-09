from django import forms
from django.utils import timezone
from apps.customers.models import Customer, Site
from .models import Precheck


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
    building_type = forms.ChoiceField(
        choices=Site._meta.get_field('building_type').choices,
        label="Gebäudetyp",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    construction_year = forms.IntegerField(
        required=False,
        label="Baujahr",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1990'})
    )
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
    distance_meter_to_hak = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        label="Entfernung Zählerschrank zu HAK (m)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '5.0'})
    )
    
    # Fotos
    meter_cabinet_photo = forms.ImageField(
        required=False,
        label="Foto Zählerschrank",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png'})
    )
    hak_photo = forms.ImageField(
        required=False,
        label="Foto Hausanschlusskasten",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png'})
    )
    location_photo = forms.ImageField(
        required=False,
        label="Foto Montageorte",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png'})
    )
    cable_route_photo = forms.ImageField(
        required=False,
        label="Foto Kabelwege",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png'})
    )
    
    # Precheck-Daten
    desired_power_kw = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        label="Gewünschte WR-Leistung (kW)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '3.0'})
    )
    inverter_class = forms.ChoiceField(
        choices=Precheck.INVERTER_CLASSES,
        label="Wechselrichter-Klasse",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    storage_kwh = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        required=False,
        label="Gewünschte Speicherkapazität (kWh)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '10.0'})
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
    own_components = forms.BooleanField(
        required=False,
        label="Ich bringe eigene Komponenten mit",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
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

    def save(self):
        """Erstelle Customer, Site und Precheck aus Formulardaten"""
        # IP-Adresse würde normalerweise aus request.META['REMOTE_ADDR'] kommen
        consent_ip = '127.0.0.1'  # Placeholder
        
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
        site = Site.objects.create(
            customer=customer,
            address=self.cleaned_data.get('customer_address', ''),
            building_type=self.cleaned_data['building_type'],
            construction_year=self.cleaned_data['construction_year'],
            main_fuse_ampere=self.cleaned_data['main_fuse_ampere'],
            grid_type=self.cleaned_data.get('grid_type') or '',
            distance_meter_to_hak=self.cleaned_data['distance_meter_to_hak'],
            meter_cabinet_photo=self.cleaned_data['meter_cabinet_photo'],
            hak_photo=self.cleaned_data['hak_photo']
        )
        
        has_wallbox = self.cleaned_data.get('has_wallbox', False)
        wallbox_cable_length = self.cleaned_data.get('wallbox_cable_length')
        if not has_wallbox:
            wallbox_power = ''
            wallbox_mount = ''
            wallbox_cable_prepared = False
            wallbox_cable_length = None
        else:
            wallbox_power = self.cleaned_data.get('wallbox_power') or ''
            wallbox_mount = self.cleaned_data.get('wallbox_mount') or ''
            wallbox_cable_prepared = self.cleaned_data.get('wallbox_cable_installed', False)
            if wallbox_cable_prepared:
                wallbox_cable_length = None

        # Precheck erstellen mit File-Uploads
        precheck = Precheck.objects.create(
            site=site,
            desired_power_kw=self.cleaned_data['desired_power_kw'],
            inverter_class=self.cleaned_data['inverter_class'],
            storage_kwh=self.cleaned_data['storage_kwh'],
            own_components=self.cleaned_data['own_components'],
            wallbox=has_wallbox,
            wallbox_class=wallbox_power,
            wallbox_mount=wallbox_mount,
            wallbox_cable_prepared=wallbox_cable_prepared,
            wallbox_cable_length_m=wallbox_cable_length,
            notes=self.cleaned_data['notes'],
            # File Uploads
            meter_cabinet_photo=self.cleaned_data.get('meter_cabinet_photo'),
            hak_photo=self.cleaned_data.get('hak_photo'),
            location_photo=self.cleaned_data.get('location_photo'),
            cable_route_photo=self.cleaned_data.get('cable_route_photo')
        )

        return precheck





