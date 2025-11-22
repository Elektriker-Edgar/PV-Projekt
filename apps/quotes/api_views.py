from typing import Dict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from .models import Component, Precheck, Quote
from .pricing import (
    pricing_input_from_request,
    calculate_pricing,
    pricing_to_response,
)


# Placeholders to satisfy router imports. Minimal list() returning JSON.
class ComponentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Component.objects.all()
    serializer_class = None

    def list(self, request, *args, **kwargs):
        data = [
            {
                'id': c.id,
                'name': c.name,
                'type': c.type,
                'vendor': c.vendor,
                'sku': c.sku,
                'unit_price': str(c.unit_price),
            }
            for c in self.get_queryset()
        ]
        return JsonResponse(data, safe=False)


class PrecheckViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Precheck.objects.all()
    serializer_class = None

    def _serialize_precheck(self, precheck, request):
        """Serialisiert einen Precheck mit selbstsprechenden Beschreibungen für Choices"""
        return {
            'id': precheck.id,

            # === KUNDENDATEN (vollständig) ===
            'customer': {
                'id': precheck.site.customer.id if precheck.site and precheck.site.customer else None,
                'name': precheck.site.customer.name if precheck.site and precheck.site.customer else None,
                'email': precheck.site.customer.email if precheck.site and precheck.site.customer else None,
                'phone': precheck.site.customer.phone if precheck.site and precheck.site.customer else None,
                'company': precheck.site.customer.company if precheck.site and precheck.site.customer else None,
                'created_at': precheck.site.customer.created_at.isoformat() if precheck.site and precheck.site.customer else None,
            } if precheck.site and precheck.site.customer else None,

            # === STANDORTDATEN (vollständig) ===
            'site': {
                'id': precheck.site.id if precheck.site else None,
                'address': precheck.site.address if precheck.site else None,
                'building_type': {
                    'value': precheck.site.building_type,
                    'display': precheck.site.get_building_type_display()
                } if precheck.site and precheck.site.building_type else None,
                'main_fuse_ampere': precheck.site.main_fuse_ampere if precheck.site else None,
                'grid_type': {
                    'value': precheck.site.grid_type,
                    'display': precheck.site.get_grid_type_display()
                } if precheck.site and precheck.site.grid_type else None,
                'distance_meter_to_hak': str(precheck.site.distance_meter_to_hak) if precheck.site and precheck.site.distance_meter_to_hak else None,
            } if precheck.site else None,

            # === GEBÄUDE & BAUZUSTAND ===
            'building_type': {
                'value': precheck.building_type,
                'display': precheck.get_building_type_display()
            } if precheck.building_type else None,
            'construction_year': precheck.construction_year,
            'has_renovation': precheck.has_renovation,
            'renovation_year': precheck.renovation_year,

            # === ELEKTRISCHE INSTALLATION ===
            'has_sls_switch': precheck.has_sls_switch,
            'sls_switch_details': precheck.sls_switch_details,
            'has_surge_protection_ac': precheck.has_surge_protection_ac,
            'surge_protection_ac_details': precheck.surge_protection_ac_details,
            'has_surge_protection_dc': precheck.has_surge_protection_dc,
            'has_grounding': {
                'value': precheck.has_grounding,
                'display': precheck.get_has_grounding_display()
            } if precheck.has_grounding else None,
            'has_deep_earth': {
                'value': precheck.has_deep_earth,
                'display': precheck.get_has_deep_earth_display()
            } if precheck.has_deep_earth else None,
            'grounding_details': precheck.grounding_details,

            # === MONTAGEORTE & KABELWEGE ===
            'inverter_location': {
                'value': precheck.inverter_location,
                'display': precheck.get_inverter_location_display()
            } if precheck.inverter_location else None,
            'storage_location': {
                'value': precheck.storage_location,
                'display': precheck.get_storage_location_display()
            } if precheck.storage_location else None,
            'distance_meter_to_inverter': str(precheck.distance_meter_to_inverter) if precheck.distance_meter_to_inverter else None,
            'grid_operator': precheck.grid_operator,

            # === PV-SYSTEM & KOMPONENTEN ===
            'desired_power_kw': str(precheck.desired_power_kw) if precheck.desired_power_kw else None,
            'storage_kwh': str(precheck.storage_kwh) if precheck.storage_kwh else None,
            'feed_in_mode': {
                'value': precheck.feed_in_mode,
                'display': precheck.get_feed_in_mode_display()
            } if precheck.feed_in_mode else None,
            'requires_backup_power': precheck.requires_backup_power,
            'backup_power_details': precheck.backup_power_details,
            'own_components': precheck.own_components,
            'own_material_description': precheck.own_material_description,

            # === ZUSATZGERÄTE ===
            'has_heat_pump': precheck.has_heat_pump,
            'heat_pump_cascade': precheck.heat_pump_cascade,
            'heat_pump_details': precheck.heat_pump_details,

            # Wallbox
            'wallbox': precheck.wallbox,
            'wallbox_class': {
                'value': precheck.wallbox_class,
                'display': precheck.get_wallbox_class_display()
            } if precheck.wallbox_class else None,
            'wallbox_mount': {
                'value': precheck.wallbox_mount,
                'display': precheck.get_wallbox_mount_display()
            } if precheck.wallbox_mount else None,
            'wallbox_cable_prepared': precheck.wallbox_cable_prepared,
            'wallbox_cable_length_m': str(precheck.wallbox_cable_length_m) if precheck.wallbox_cable_length_m else None,
            'wallbox_pv_surplus': precheck.wallbox_pv_surplus,

            # === PAKET & EXPRESS ===
            'package_choice': {
                'value': precheck.package_choice,
                'display': precheck.get_package_choice_display()
            } if precheck.package_choice else None,
            'is_express_package': precheck.is_express_package,

            # === FOTOS & UPLOADS ===
            'photos': [
                {
                    'id': photo.id,
                    'category': photo.category,
                    'category_display': photo.get_category_display(),
                    'url': request.build_absolute_uri(photo.photo.url) if photo.photo else None,
                    'uploaded_at': photo.uploaded_at.isoformat(),
                }
                for photo in precheck.photos.all()
            ],
            'has_photos': precheck.photos.exists(),
            'photo_count': precheck.photos.count(),

            # Legacy-Foto-Felder (für Rückwärtskompatibilität)
            'meter_cabinet_photo': request.build_absolute_uri(precheck.meter_cabinet_photo.url) if precheck.meter_cabinet_photo else None,
            'hak_photo': request.build_absolute_uri(precheck.hak_photo.url) if precheck.hak_photo else None,
            'location_photo': request.build_absolute_uri(precheck.location_photo.url) if precheck.location_photo else None,
            'cable_route_photo': request.build_absolute_uri(precheck.cable_route_photo.url) if precheck.cable_route_photo else None,

            # === TERMINWÜNSCHE ===
            'preferred_timeframes': precheck.preferred_timeframes,

            # === NOTIZEN ===
            'notes': precheck.notes,

            # === METADATEN ===
            'created_at': precheck.created_at.isoformat(),
            'updated_at': precheck.updated_at.isoformat(),
        }

    def list(self, request, *args, **kwargs):
        prechecks = self.get_queryset().select_related(
            'site__customer'
        ).prefetch_related('photos')
        data = [self._serialize_precheck(p, request) for p in prechecks]
        return JsonResponse(data, safe=False)

    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            precheck = self.get_queryset().select_related(
                'site__customer'
            ).prefetch_related('photos').get(pk=pk)
            data = self._serialize_precheck(precheck, request)
            return JsonResponse(data)
        except Precheck.DoesNotExist:
            return JsonResponse({'error': 'Precheck nicht gefunden'}, status=404)


class QuoteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quote.objects.all()
    serializer_class = None

    def list(self, request, *args, **kwargs):
        return JsonResponse([], safe=False)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def pricing_preview(request):
    payload: Dict = request.data if hasattr(request, 'data') else request.POST
    pricing_input = pricing_input_from_request(payload)
    pricing = calculate_pricing(pricing_input)
    return JsonResponse(pricing_to_response(pricing))


@api_view(['POST'])
def create_precheck(request):
    return JsonResponse({'detail': 'not implemented'}, status=501)


@api_view(['POST'])
def approve_quote(request, pk):
    return JsonResponse({'detail': 'not implemented'}, status=501)

