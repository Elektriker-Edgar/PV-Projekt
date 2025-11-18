"""
N8n Integration Forms
Forms für Konfiguration und Testing
"""

from django import forms
from apps.integrations.models import N8nConfiguration


class N8nConfigurationForm(forms.ModelForm):
    """Form für N8n Konfiguration"""

    class Meta:
        model = N8nConfiguration
        fields = ['webhook_url', 'api_key', 'is_active']
        widgets = {
            'webhook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'http://localhost:5678/webhook/precheck-submitted'
            }),
            'api_key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional API Key'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'webhook_url': 'N8n Webhook URL',
            'api_key': 'API Key (optional)',
            'is_active': 'N8n Integration aktiviert',
        }
        help_texts = {
            'webhook_url': 'Die URL des N8n Webhooks, an den Django Ereignisse sendet',
            'api_key': 'Optionaler API-Schlüssel für die Authentifizierung',
            'is_active': 'Wenn deaktiviert, werden keine Webhooks gesendet',
        }


class WebhookTestForm(forms.Form):
    """Form für manuellen Webhook-Test"""

    precheck_id = forms.IntegerField(
        label='Precheck ID',
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'z.B. 123',
            'min': '1'
        }),
        help_text='ID eines existierenden Prechecks aus der Datenbank'
    )
