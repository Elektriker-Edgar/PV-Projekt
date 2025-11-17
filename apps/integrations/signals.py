"""
N8n Integration Signals
=======================

Signal-Handler für automatische Webhook-Trigger an N8n.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from apps.quotes.models import Precheck
from apps.integrations.models import WebhookLog, N8nWorkflowStatus

import requests
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Precheck)
def precheck_submitted_handler(sender, instance, created, **kwargs):
    """
    Wird ausgelöst wenn ein neuer Precheck gespeichert wird.

    Sendet Webhook an N8n mit der Precheck-ID.
    N8n kann dann über die API die vollständigen Daten abrufen.

    **Trigger:** Neuer Precheck wird erstellt
    **Action:** POST-Request an N8n Webhook
    **Payload:** Minimale Daten (nur IDs), N8n holt Rest via API
    """

    # Nur bei neuen Prechecks triggern
    if not created:
        return

    # Nur wenn N8n konfiguriert ist
    n8n_webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', None)
    if not n8n_webhook_url:
        logger.warning("N8N_WEBHOOK_URL nicht konfiguriert - Webhook wird nicht gesendet")
        return

    # Payload vorbereiten (minimal, N8n holt Rest via API)
    payload = {
        'event': 'precheck_submitted',
        'precheck_id': instance.id,

        # Callback-URL für N8n
        'api_base_url': getattr(settings, 'BASE_URL', 'http://192.168.178.30:8025'),
        'api_endpoints': {
            'precheck_data': f'/api/integrations/precheck/{instance.id}/',
            'pricing_data': '/api/integrations/pricing/',
        },

        # Minimale Metadaten (für Logging/Routing in N8n)
        'metadata': {
            'customer_email': instance.customer.email if instance.customer else None,
            'has_customer': bool(instance.customer),
            'has_site': bool(instance.site),
            'timestamp': instance.created_at.isoformat(),
        }
    }

    # Webhook-Log erstellen (pending)
    webhook_log = WebhookLog.objects.create(
        event_type='precheck_submitted',
        direction='outgoing',
        status='pending',
        precheck_id=instance.id,
        payload=payload,
    )

    # Workflow-Status erstellen
    workflow_status = N8nWorkflowStatus.objects.create(
        precheck=instance,
        status='initiated',
        metadata={'webhook_log_id': webhook_log.id}
    )

    try:
        # Webhook an N8n senden
        logger.info(f"Sende Webhook an N8n für Precheck {instance.id}")

        response = requests.post(
            n8n_webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                # API-Key für Authentifizierung (optional)
                'X-API-KEY': getattr(settings, 'N8N_API_KEY', ''),
            },
            timeout=10  # 10 Sekunden Timeout
        )

        response.raise_for_status()  # Raise exception bei HTTP-Fehler

        # Erfolg
        webhook_log.mark_success(response_data={
            'status_code': response.status_code,
            'response': response.json() if response.content else None,
        })

        workflow_status.update_status('data_validation', {
            'webhook_sent': True,
            'n8n_response': response.json() if response.content else None,
        })

        logger.info(f"Webhook erfolgreich an N8n gesendet: Precheck {instance.id}")

    except requests.exceptions.Timeout:
        error_msg = "N8n Webhook Timeout (>10s)"
        webhook_log.mark_failed(error_msg)
        workflow_status.update_status('failed', {'error': error_msg})
        logger.error(f"{error_msg} - Precheck {instance.id}")

    except requests.exceptions.ConnectionError as e:
        error_msg = f"N8n nicht erreichbar: {str(e)}"
        webhook_log.mark_failed(error_msg)
        workflow_status.update_status('failed', {'error': error_msg})
        logger.error(f"{error_msg} - Precheck {instance.id}")

    except requests.exceptions.HTTPError as e:
        error_msg = f"N8n HTTP Error: {e.response.status_code} - {e.response.text}"
        webhook_log.mark_failed(error_msg)
        workflow_status.update_status('failed', {'error': error_msg})
        logger.error(f"{error_msg} - Precheck {instance.id}")

    except Exception as e:
        error_msg = f"Unerwarteter Fehler beim Webhook-Senden: {str(e)}"
        webhook_log.mark_failed(error_msg)
        workflow_status.update_status('failed', {'error': error_msg})
        logger.error(f"{error_msg} - Precheck {instance.id}", exc_info=True)


# ============================================================================
# OPTIONAL: Quote-Approval Webhook (für später)
# ============================================================================

# @receiver(post_save, sender=Quote)
# def quote_approved_handler(sender, instance, created, **kwargs):
#     """
#     Wird ausgelöst wenn ein Quote auf 'approved' gesetzt wird.
#     Sendet Webhook an N8n um PDF-Generierung und Versand zu triggern.
#     """
#
#     # Nur bei Statusänderung auf 'approved'
#     if created or instance.status != 'approved':
#         return
#
#     # TODO: Implementieren wenn Quote-Approval-Workflow aktiv ist
#     pass
