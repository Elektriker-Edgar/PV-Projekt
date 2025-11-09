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
        label="Telefon", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+49 40 12345678'})
    )
    customer_type = forms.ChoiceField(
        choices=Customer.CUSTOMER_TYPES,
        label="Kundentyp",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    customer_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Straße, PLZ Ort'})
    )
    
    # Site-Daten
    site_address = forms.CharField(
        label="Installationsadresse",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Installationsort (falls abweichend)'})
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
        label="Netzform",
        widget=forms.Select(attrs={'class': 'form-control'})
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
    
    def save(self):
        """Erstelle Customer, Site und Precheck aus Formulardaten"""
        # IP-Adresse würde normalerweise aus request.META['REMOTE_ADDR'] kommen
        consent_ip = '127.0.0.1'  # Placeholder
        
        # Customer erstellen
        customer = Customer.objects.create(
            name=self.cleaned_data['customer_name'],
            email=self.cleaned_data['customer_email'],
            phone=self.cleaned_data['customer_phone'],
            customer_type=self.cleaned_data['customer_type'],
            address=self.cleaned_data['customer_address'],
            consent_timestamp=timezone.now(),
            consent_ip=consent_ip
        )
        
        # Site erstellen
        site = Site.objects.create(
            customer=customer,
            address=self.cleaned_data['site_address'] or self.cleaned_data['customer_address'],
            building_type=self.cleaned_data['building_type'],
            construction_year=self.cleaned_data['construction_year'],
            main_fuse_ampere=self.cleaned_data['main_fuse_ampere'],
            grid_type=self.cleaned_data['grid_type'],
            distance_meter_to_hak=self.cleaned_data['distance_meter_to_hak'],
            meter_cabinet_photo=self.cleaned_data['meter_cabinet_photo'],
            hak_photo=self.cleaned_data['hak_photo']
        )
        
        # Precheck erstellen mit File-Uploads
        precheck = Precheck.objects.create(
            site=site,
            desired_power_kw=self.cleaned_data['desired_power_kw'],
            inverter_class=self.cleaned_data['inverter_class'],
            storage_kwh=self.cleaned_data['storage_kwh'],
            own_components=self.cleaned_data['own_components'],
            notes=self.cleaned_data['notes'],
            # File Uploads
            meter_cabinet_photo=self.cleaned_data.get('meter_cabinet_photo'),
            hak_photo=self.cleaned_data.get('hak_photo'),
            location_photo=self.cleaned_data.get('location_photo'),
            cable_route_photo=self.cleaned_data.get('cable_route_photo')
        )

        return precheck