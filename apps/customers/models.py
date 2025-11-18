from django.db import models
from django.utils import timezone
from apps.quotes.validators import validate_media_file
from apps.core.choices import BuildingType, GridType


class Customer(models.Model):
    """Kunde"""
    CUSTOMER_TYPES = [
        ('private', 'Privatperson'),
        ('business', 'Gewerbe'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='private')
    address = models.TextField(blank=True)
    last_quote_number = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Zuletzt erzeugte Angebotsnummer"
    )
    
    # DSGVO
    consent_timestamp = models.DateTimeField()
    consent_ip = models.GenericIPAddressField()
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Für Suche nach Email und Name
            models.Index(fields=['email'], name='customer_email_idx'),
            models.Index(fields=['name'], name='customer_name_idx'),
            models.Index(fields=['customer_type', '-created_at'], name='customer_type_date_idx'),
        ]

    def __str__(self):
        return self.name


class Site(models.Model):
    """Installationsort"""
    GRID_TYPES = GridType.choices

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sites')
    address = models.TextField()
    building_type = models.CharField(
        max_length=50,
        choices=BuildingType.choices,
    )
    construction_year = models.PositiveIntegerField(null=True, blank=True)
    main_fuse_ampere = models.PositiveIntegerField(help_text="Hauptsicherung in Ampere")
    grid_type = models.CharField(max_length=10, choices=GRID_TYPES, blank=True)
    distance_meter_to_hak = models.DecimalField(max_digits=5, decimal_places=2, 
                                               help_text="Entfernung Zählerschrank zu HAK in Metern")
    
    # Fotos / Dokumente
    meter_cabinet_photo = models.FileField(
        upload_to='uploads/meter_cabinets/',
        null=True,
        blank=True,
        validators=[validate_media_file],
        help_text="Datei Zählerschrank (JPG, PNG oder PDF, max 5MB)"
    )
    hak_photo = models.FileField(
        upload_to='uploads/hak/',
        null=True,
        blank=True,
        validators=[validate_media_file],
        help_text="Datei Hausanschlusskasten (JPG, PNG oder PDF, max 5MB)"
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Für Filterung nach Kunde und Gebäudetyp
            models.Index(fields=['customer', '-created_at'], name='site_customer_date_idx'),
            models.Index(fields=['building_type'], name='site_building_idx'),
        ]

    def __str__(self):
        return f"{self.customer.name} - {self.address}"
