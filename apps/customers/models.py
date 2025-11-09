from django.db import models
from django.utils import timezone


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

    def __str__(self):
        return self.name


class Site(models.Model):
    """Installationsort"""
    GRID_TYPES = [
        ('TN-C', 'TN-C'),
        ('TN-S', 'TN-S'),
        ('TT', 'TT'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sites')
    address = models.TextField()
    building_type = models.CharField(max_length=50, choices=[
        ('efh', 'Einfamilienhaus'),
        ('mfh', 'Mehrfamilienhaus'),
        ('commercial', 'Gewerbe')
    ])
    construction_year = models.PositiveIntegerField(null=True, blank=True)
    main_fuse_ampere = models.PositiveIntegerField(help_text="Hauptsicherung in Ampere")
    grid_type = models.CharField(max_length=10, choices=GRID_TYPES)
    distance_meter_to_hak = models.DecimalField(max_digits=5, decimal_places=2, 
                                               help_text="Entfernung Zählerschrank zu HAK in Metern")
    
    # Fotos
    meter_cabinet_photo = models.ImageField(upload_to='uploads/meter_cabinets/', null=True, blank=True)
    hak_photo = models.ImageField(upload_to='uploads/hak/', null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} - {self.address}"
