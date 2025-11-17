"""
N8n Integration API URLs
========================

Alle API-Endpoints für die N8n-Integration.
"""

from django.urls import path
from apps.integrations import api_views

app_name = 'integrations'

urlpatterns = [
    # ========================================================================
    # HAUPTENDPOINTS für N8n
    # ========================================================================

    # Precheck-Daten abrufen
    path(
        'precheck/<int:precheck_id>/',
        api_views.get_precheck_data,
        name='get_precheck_data'
    ),

    # Preisdaten abrufen
    path(
        'pricing/',
        api_views.get_pricing_data,
        name='get_pricing_data'
    ),

    # Produktkategorien abrufen
    path(
        'categories/',
        api_views.get_product_categories,
        name='get_product_categories'
    ),

    # ========================================================================
    # TEST-ENDPOINTS
    # ========================================================================

    # Test-Webhook-Empfänger
    path(
        'test/webhook/',
        api_views.test_webhook_receiver,
        name='test_webhook'
    ),
]
