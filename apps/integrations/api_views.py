"""
N8n Integration API Views
=========================

Diese API-Endpoints ermöglichen N8n den Zugriff auf Django-Daten
für die automatisierte Angebotserstellung.

WICHTIG: Für Tests ohne Authentifizierung (intern).
         In Production: API-Key-Authentifizierung hinzufügen!
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.quotes.models import Precheck, Product, ProductCategory
from apps.integrations.models import WebhookLog

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# PRECHECK API - Kundendaten für N8n
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: In Production mit API-Key absichern
def get_precheck_data(request, precheck_id):
    """
    Liefert alle Daten eines Prechecks für N8n.

    **Endpoint:** GET /api/integrations/precheck/<id>/

    **Response:**
    {
        "precheck_id": 123,
        "customer": {...},
        "site": {...},
        "project": {...},
        "pricing": {...},
        "completeness": {...},
        "metadata": {...}
    }

    **Use Case:**
    N8n ruft diese URL auf nachdem Webhook über neuen Precheck informiert hat.
    KI-Agent nutzt die Daten um Vollständigkeit zu prüfen.
    """

    try:
        # Precheck laden mit allen Relationen
        precheck = Precheck.objects.select_related(
            'customer',
            'site',
        ).prefetch_related(
            'site__precheck_photos'
        ).get(id=precheck_id)

        # Log API-Call
        WebhookLog.objects.create(
            event_type='precheck_data_requested',
            direction='incoming',
            status='success',
            precheck_id=precheck.id,
            payload={'precheck_id': precheck_id, 'requester': 'n8n'},
            response={'status': 'data_returned'},
        )

        # Daten strukturiert aufbereiten
        response_data = {
            'precheck_id': precheck.id,

            # Kundendaten
            'customer': {
                'id': precheck.site.customer.id if (precheck.site and precheck.site.customer) else None,
                'name': precheck.site.customer.name if (precheck.site and precheck.site.customer) else None,
                'email': precheck.site.customer.email if (precheck.site and precheck.site.customer) else None,
                'phone': precheck.site.customer.phone if (precheck.site and precheck.site.customer) else None,
            } if (precheck.site and precheck.site.customer) else None,

            # Standortdaten
            'site': {
                'id': precheck.site.id if precheck.site else None,
                'address': precheck.site.address if precheck.site else None,
                'building_type': precheck.site.building_type if precheck.site else None,
                'main_fuse_ampere': precheck.site.main_fuse_ampere if precheck.site else None,
                'grid_type': precheck.site.grid_type if precheck.site else None,
                'grid_operator': precheck.site.grid_operator if precheck.site else None,

                # Fotos
                'has_photos': precheck.site.precheck_photos.exists() if precheck.site else False,
                'photo_count': precheck.site.precheck_photos.count() if precheck.site else 0,
                'photos': [
                    {
                        'id': photo.id,
                        'category': photo.category,
                        'url': request.build_absolute_uri(photo.image.url) if photo.image else None,
                    }
                    for photo in precheck.site.precheck_photos.all()
                ] if precheck.site else [],
            } if precheck.site else None,

            # Projektdaten
            'project': {
                'desired_power_kw': precheck.form_data.get('desired_power_kw'),
                'storage_kwh': precheck.form_data.get('storage_kwh', 0),
                'has_storage': float(precheck.form_data.get('storage_kwh', 0)) > 0,

                # Wallbox
                'has_wallbox': precheck.form_data.get('has_wallbox', False),
                'wallbox_power': precheck.form_data.get('wallbox_power'),
                'wallbox_mount': precheck.form_data.get('wallbox_mount'),
                'wallbox_cable_length': precheck.form_data.get('wallbox_cable_length'),
                'wallbox_pv_surplus': precheck.form_data.get('wallbox_pv_surplus', False),

                # Komponenten
                'own_components': precheck.form_data.get('own_components', False),

                # Distanzen
                'distance_meter_to_inverter': precheck.form_data.get('distance_meter_to_inverter'),
                'distance_meter_to_hak': precheck.form_data.get('distance_meter_to_hak'),

                # Locations
                'inverter_location': precheck.form_data.get('inverter_location'),
                'storage_location': precheck.form_data.get('storage_location'),

                # Notizen
                'customer_notes': precheck.form_data.get('notes', ''),
            },

            # Preisdaten
            'pricing': precheck.price_data or {},

            # Vollständigkeits-Check (für KI)
            'completeness': {
                'has_customer_data': bool(precheck.site and precheck.site.customer),
                'has_customer_email': bool(precheck.site and precheck.site.customer and precheck.site.customer.email),
                'has_customer_phone': bool(precheck.site and precheck.site.customer and precheck.site.customer.phone),

                'has_site_data': bool(precheck.site),
                'has_site_address': bool(precheck.site and precheck.site.address),
                'has_main_fuse': bool(precheck.site and precheck.site.main_fuse_ampere),
                'has_grid_type': bool(precheck.site and precheck.site.grid_type),

                'has_photos': precheck.site.precheck_photos.exists() if precheck.site else False,
                'has_meter_photo': precheck.site.precheck_photos.filter(category='meter_cabinet').exists() if precheck.site else False,
                'has_hak_photo': precheck.site.precheck_photos.filter(category='hak').exists() if precheck.site else False,

                'has_power_data': bool(precheck.form_data.get('desired_power_kw')),
                'has_pricing': bool(precheck.price_data),

                # Empfohlene Felder
                'has_inverter_location': bool(precheck.form_data.get('inverter_location')),
                'has_distance_data': bool(
                    precheck.form_data.get('distance_meter_to_inverter') or
                    precheck.form_data.get('distance_meter_to_hak')
                ),
            },

            # Metadaten
            'metadata': {
                'status': precheck.status,
                'created_at': precheck.created_at.isoformat(),
                'updated_at': precheck.updated_at.isoformat() if hasattr(precheck, 'updated_at') else None,
                'has_quote': hasattr(precheck, 'quotes') and precheck.quotes.exists(),
            },
        }

        logger.info(f"N8n requested precheck data: {precheck_id}")
        return Response(response_data)

    except Precheck.DoesNotExist:
        # Log fehlgeschlagenen Request
        WebhookLog.objects.create(
            event_type='precheck_data_requested',
            direction='incoming',
            status='failed',
            precheck_id=precheck_id,
            payload={'precheck_id': precheck_id},
            error_message='Precheck not found',
        )

        logger.warning(f"N8n requested non-existent precheck: {precheck_id}")
        return Response(
            {'error': 'Precheck nicht gefunden', 'precheck_id': precheck_id},
            status=404
        )

    except Exception as e:
        # Log unerwarteten Fehler
        WebhookLog.objects.create(
            event_type='precheck_data_requested',
            direction='incoming',
            status='failed',
            precheck_id=precheck_id,
            payload={'precheck_id': precheck_id},
            error_message=str(e),
        )

        logger.error(f"Error in get_precheck_data: {e}", exc_info=True)
        return Response(
            {'error': 'Interner Serverfehler', 'detail': str(e)},
            status=500
        )


# ============================================================================
# PRICING API - Preisdaten für N8n
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: In Production mit API-Key absichern
def get_pricing_data(request):
    """
    Liefert Preisdaten aus dem Produktkatalog für N8n.

    **Endpoint:** GET /api/integrations/pricing/

    **Query Parameters:**
    - categories (optional): Komma-separierte Liste von Kategorien
      Beispiel: ?categories=Wechselrichter,Speicher

    - skus (optional): Komma-separierte Liste von SKUs
      Beispiel: ?skus=PCHK-INVERTER-TIER-5,PCHK-STORAGE-TIER-3

    - search (optional): Suchbegriff für Name oder SKU
      Beispiel: ?search=Wallbox

    **Response:**
    {
        "products": [
            {
                "id": 1,
                "sku": "PCHK-INVERTER-TIER-5",
                "name": "Wechselrichter 5kW Installation",
                "category": "Precheck-Artikel",
                "sales_price_net": 1500.00,
                "vat_rate": 0.19,
                "sales_price_gross": 1785.00,
                "unit": "Pauschal"
            },
            ...
        ],
        "count": 42
    }

    **Use Case:**
    N8n holt Preise für Kalkulation und Angebotserstellung.
    """

    try:
        # Query-Parameter auslesen
        categories_param = request.GET.get('categories', '')
        skus_param = request.GET.get('skus', '')
        search_param = request.GET.get('search', '')

        # Basis-Query: Nur aktive Produkte
        products = Product.objects.filter(is_active=True).select_related('category')

        # Filter nach Kategorien
        if categories_param:
            category_names = [c.strip() for c in categories_param.split(',')]
            products = products.filter(category__name__in=category_names)

        # Filter nach SKUs
        if skus_param:
            skus = [s.strip() for s in skus_param.split(',')]
            products = products.filter(sku__in=skus)

        # Suche
        if search_param:
            products = products.filter(
                Q(name__icontains=search_param) |
                Q(sku__icontains=search_param) |
                Q(description__icontains=search_param)
            )

        # Daten aufbereiten
        products_data = [
            {
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'description': product.description,
                'category': product.category.name if product.category else None,
                'category_id': product.category.id if product.category else None,

                # Preise
                'sales_price_net': float(product.sales_price_net),
                'sales_price_gross': float(product.sales_price_gross),
                'purchase_price_net': float(product.purchase_price_net),
                'vat_rate': float(product.vat_rate),

                # Weitere Daten
                'unit': product.unit,
                'manufacturer': product.manufacturer,
                'supplier': product.supplier,

                # Lagerbestand (optional)
                'stock_quantity': product.stock_quantity,
                'min_stock_level': product.min_stock_level,
            }
            for product in products
        ]

        # Log API-Call
        WebhookLog.objects.create(
            event_type='pricing_data_requested',
            direction='incoming',
            status='success',
            payload={
                'categories': categories_param,
                'skus': skus_param,
                'search': search_param,
            },
            response={'count': len(products_data)},
        )

        logger.info(f"N8n requested pricing data: {len(products_data)} products returned")

        return Response({
            'products': products_data,
            'count': len(products_data),
            'filters_applied': {
                'categories': categories_param,
                'skus': skus_param,
                'search': search_param,
            }
        })

    except Exception as e:
        # Log Fehler
        WebhookLog.objects.create(
            event_type='pricing_data_requested',
            direction='incoming',
            status='failed',
            payload=dict(request.GET),
            error_message=str(e),
        )

        logger.error(f"Error in get_pricing_data: {e}", exc_info=True)
        return Response(
            {'error': 'Interner Serverfehler', 'detail': str(e)},
            status=500
        )


# ============================================================================
# HELPER API - Produktkategorien
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_categories(request):
    """
    Liefert alle Produktkategorien.

    **Endpoint:** GET /api/integrations/categories/

    **Response:**
    {
        "categories": [
            {"id": 1, "name": "Precheck-Artikel", "product_count": 15},
            {"id": 2, "name": "Wechselrichter", "product_count": 8},
            ...
        ]
    }
    """

    categories = ProductCategory.objects.filter(is_active=True)

    categories_data = [
        {
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'sort_order': cat.sort_order,
            'product_count': cat.products.filter(is_active=True).count(),
        }
        for cat in categories
    ]

    return Response({
        'categories': categories_data,
        'count': len(categories_data),
    })


# ============================================================================
# TEST ENDPOINT - Webhook-Empfang testen
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def test_webhook_receiver(request):
    """
    Test-Endpoint um Webhooks von N8n zu empfangen.

    **Endpoint:** POST /api/integrations/test/webhook/

    **Body:** Beliebige JSON-Daten

    **Response:**
    {
        "status": "received",
        "payload": {...},
        "webhook_log_id": 123
    }

    **Use Case:**
    N8n sendet Test-Webhook um Verbindung zu prüfen.
    """

    payload = request.data

    # Log Webhook
    log = WebhookLog.objects.create(
        event_type='test_webhook',
        direction='incoming',
        status='success',
        payload=payload,
        response={'status': 'acknowledged'},
    )

    logger.info(f"Test webhook received from N8n: {payload}")

    return Response({
        'status': 'received',
        'message': 'Webhook erfolgreich empfangen',
        'payload': payload,
        'webhook_log_id': log.id,
        'timestamp': log.created_at.isoformat(),
    })
