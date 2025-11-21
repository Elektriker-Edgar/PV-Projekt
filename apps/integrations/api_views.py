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
from apps.quotes.pricing import calculate_pricing, PricingInput  # Für on-the-fly Preisberechnung
from decimal import Decimal

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
        # WICHTIG: Precheck hat keine direkte 'customer' Beziehung!
        # Korrekte Struktur: Precheck → Site → Customer
        # Fotos hängen direkt am Precheck (nicht am Site)
        precheck = Precheck.objects.select_related(
            'site',
            'site__customer',  # Customer über Site laden
        ).prefetch_related(
            'photos'  # PrecheckPhoto-Model mit related_name='photos'
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
                'building_type': {
                    'value': precheck.site.building_type,
                    'display': precheck.site.get_building_type_display()
                } if (precheck.site and precheck.site.building_type) else None,
                'main_fuse_ampere': precheck.site.main_fuse_ampere if precheck.site else None,
                'grid_type': {
                    'value': precheck.site.grid_type,
                    'display': precheck.site.get_grid_type_display()
                } if (precheck.site and precheck.site.grid_type) else None,
                'distance_meter_to_hak': float(precheck.site.distance_meter_to_hak) if (precheck.site and precheck.site.distance_meter_to_hak) else None,

                # Fotos (hängen direkt am Precheck, nicht am Site)
                'has_photos': precheck.photos.exists(),
                'photo_count': precheck.photos.count(),
                'photos': [
                    {
                        'id': photo.id,
                        'category': photo.category,
                        'category_display': photo.get_category_display(),
                        'url': request.build_absolute_uri(photo.photo.url) if photo.photo else None,
                    }
                    for photo in precheck.photos.all()
                ],
            } if precheck.site else None,

            # Projektdaten (aus individuellen Feldern)
            'project': {
                'desired_power_kw': float(precheck.desired_power_kw) if precheck.desired_power_kw else None,
                'storage_kwh': float(precheck.storage_kwh) if precheck.storage_kwh else 0,
                'has_storage': bool(precheck.storage_kwh and precheck.storage_kwh > 0),

                # Wallbox mit Display-Namen
                'has_wallbox': precheck.wallbox,
                'wallbox_class': {
                    'value': precheck.wallbox_class,
                    'display': precheck.get_wallbox_class_display()
                } if precheck.wallbox_class else None,
                'wallbox_mount': {
                    'value': precheck.wallbox_mount,
                    'display': precheck.get_wallbox_mount_display()
                } if precheck.wallbox_mount else None,
                'wallbox_cable_length': float(precheck.wallbox_cable_length_m) if precheck.wallbox_cable_length_m else None,
                'wallbox_cable_prepared': precheck.wallbox_cable_prepared,
                'wallbox_pv_surplus': precheck.wallbox_pv_surplus,

                # Komponenten
                'own_components': precheck.own_components,
                'own_material_description': precheck.own_material_description,

                # Distanzen
                'distance_meter_to_inverter': float(precheck.distance_meter_to_inverter) if precheck.distance_meter_to_inverter else None,

                # Locations mit Display-Namen
                'inverter_location': {
                    'value': precheck.inverter_location,
                    'display': precheck.get_inverter_location_display()
                } if precheck.inverter_location else None,
                'storage_location': {
                    'value': precheck.storage_location,
                    'display': precheck.get_storage_location_display()
                } if precheck.storage_location else None,

                # Weitere Details mit Display-Namen
                'building_type': {
                    'value': precheck.building_type,
                    'display': precheck.get_building_type_display()
                } if precheck.building_type else None,
                'feed_in_mode': {
                    'value': precheck.feed_in_mode,
                    'display': precheck.get_feed_in_mode_display()
                } if precheck.feed_in_mode else None,
                'requires_backup_power': precheck.requires_backup_power,
                'has_heat_pump': precheck.has_heat_pump,
                'grid_operator': precheck.grid_operator,

                # Erdung mit Display-Namen
                'has_grounding': {
                    'value': precheck.has_grounding,
                    'display': precheck.get_has_grounding_display()
                } if precheck.has_grounding else None,
                'has_deep_earth': {
                    'value': precheck.has_deep_earth,
                    'display': precheck.get_has_deep_earth_display()
                } if precheck.has_deep_earth else None,

                # Notizen
                'customer_notes': precheck.notes,
            },

            # Preisdaten (on-the-fly Berechnung mit Pricing-Engine)
            'pricing': {},  # Wird unten berechnet

            # Vollständigkeits-Check (für KI)
            'completeness': {
                'has_customer_data': bool(precheck.site and precheck.site.customer),
                'has_customer_email': bool(precheck.site and precheck.site.customer and precheck.site.customer.email),
                'has_customer_phone': bool(precheck.site and precheck.site.customer and precheck.site.customer.phone),

                'has_site_data': bool(precheck.site),
                'has_site_address': bool(precheck.site and precheck.site.address),
                'has_main_fuse': bool(precheck.site and precheck.site.main_fuse_ampere),
                'has_grid_type': bool(precheck.site and precheck.site.grid_type),

                # Fotos hängen direkt am Precheck
                'has_photos': precheck.photos.exists(),
                'has_meter_photo': precheck.photos.filter(category='meter_cabinet').exists(),
                'has_hak_photo': precheck.photos.filter(category='hak').exists(),

                'has_power_data': bool(precheck.desired_power_kw),
                'has_pricing': True,  # Wird immer on-the-fly berechnet

                # Empfohlene Felder
                'has_inverter_location': bool(precheck.inverter_location),
                'has_distance_data': bool(precheck.distance_meter_to_inverter),
            },

            # Metadaten
            'metadata': {
                'created_at': precheck.created_at.isoformat(),
                'updated_at': precheck.updated_at.isoformat(),
                'has_quote': hasattr(precheck, 'quote'),  # OneToOneField ohne related_name → 'quote' (Singular)
                'quote_status': precheck.quote.status if hasattr(precheck, 'quote') else None,
                'package_choice': {
                    'value': precheck.package_choice,
                    'display': precheck.get_package_choice_display()
                } if precheck.package_choice else None,
                'is_express_package': precheck.is_express_package,
            },
        }

        # Preisberechnung on-the-fly durchführen
        try:
            pricing_input = PricingInput(
                building_type=precheck.building_type or 'efh',
                site_address=precheck.site.address if precheck.site else '',
                main_fuse_ampere=precheck.site.main_fuse_ampere if precheck.site else 35,
                grid_type=precheck.site.grid_type if precheck.site else '3p',
                distance_meter=Decimal(str(precheck.distance_meter_to_inverter)) if precheck.distance_meter_to_inverter else Decimal('0'),
                desired_power_kw=Decimal(str(precheck.desired_power_kw)) if precheck.desired_power_kw else Decimal('0'),
                storage_kwh=Decimal(str(precheck.storage_kwh)) if precheck.storage_kwh else Decimal('0'),
                own_components=precheck.own_components,
                has_wallbox=precheck.wallbox,
                wallbox_power=precheck.wallbox_class or '',
                wallbox_mount=precheck.wallbox_mount or 'wall',
                wallbox_cable_installed=precheck.wallbox_cable_prepared,
                wallbox_cable_length=Decimal(str(precheck.wallbox_cable_length_m)) if precheck.wallbox_cable_length_m else Decimal('0'),
                wallbox_pv_surplus=precheck.wallbox_pv_surplus,
            )
            pricing_result = calculate_pricing(pricing_input)
            # Decimal to float konvertieren für JSON-Serialisierung
            response_data['pricing'] = {k: float(v) for k, v in pricing_result.items()}
        except Exception as e:
            logger.error(f"Error calculating pricing for precheck {precheck_id}: {e}", exc_info=True)
            response_data['pricing'] = {
                'error': 'Preisberechnung fehlgeschlagen',
                'detail': str(e)
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
                "description": "Installation und Inbetriebnahme",
                "category": "Precheck-Artikel",
                "sales_price_net": 1500.00,
                "sales_price_gross": 1785.00,
                "vat_rate": 0.19,
                "unit": "Pauschal",
                "manufacturer": "EDGARD"
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

        # Daten aufbereiten (reduziert für n8n)
        products_data = [
            {
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'description': product.description,
                'category': product.category.name if product.category else None,
                'sales_price_net': float(product.sales_price_net),
                'sales_price_gross': float(product.sales_price_gross),
                'vat_rate': float(product.vat_rate),
                'unit': product.unit,
                'manufacturer': product.manufacturer,
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
