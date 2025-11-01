from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Erweiterte User-Modell für EDGARD PV-Service"""
    ROLES = [
        ('admin', 'Administrator'),
        ('office', 'Büro'),
        ('technician', 'Monteur'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLES, default='office')
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class AuditLog(models.Model):
    """Audit-Log für wichtige Aktionen"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    changes = models.TextField(default='{}', help_text='JSON string')
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
