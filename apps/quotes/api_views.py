from decimal import Decimal
from typing import Dict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from .models import Component, Precheck, Quote, PriceConfig


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

    def list(self, request, *args, **kwargs):
        return JsonResponse([], safe=False)


class QuoteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quote.objects.all()
    serializer_class = None

    def list(self, request, *args, **kwargs):
        return JsonResponse([], safe=False)


def _pc(key: str, default: Decimal) -> Decimal:
    try:
        obj = PriceConfig.objects.get(price_type=key)
        return obj.value
    except PriceConfig.DoesNotExist:
        return default


def _infer_travel_cost(address: str) -> Decimal:
    a = (address or '').lower()
    if 'hamburg' in a:
        return _pc('travel_zone_0', Decimal('0.00'))
    if any(x in a for x in ['norderstedt', 'ahrensburg', 'pinneberg']):
        return _pc('travel_zone_30', Decimal('50.00'))
    return _pc('travel_zone_60', Decimal('95.00'))


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def pricing_preview(request):
    data: Dict = request.data if hasattr(request, 'data') else request.POST

    site_address = data.get('site_address', '')
    main_fuse = int(data.get('main_fuse_ampere') or 0)
    grid_type = data.get('grid_type') or ''
    distance = Decimal(str(data.get('distance_meter_to_inverter') or 0))
    desired_power = Decimal(str(data.get('desired_power_kw') or 0))
    inverter_class = (data.get('inverter_class') or '').strip()
    storage_kwh = Decimal(str(data.get('storage_kwh') or 0))
    own_components = str(data.get('own_components')).lower() in ['1', 'true', 'on']

    # Wallbox parameters
    has_wallbox = str(data.get('has_wallbox')).lower() in ['1', 'true', 'on']
    wallbox_power = data.get('wallbox_power', '')  # '4kw', '11kw', '22kw'
    wallbox_mount = data.get('wallbox_mount', '')  # 'wall', 'stand'
    wallbox_cable_installed = str(data.get('wallbox_cable_installed')).lower() in ['1', 'true', 'on']
    wallbox_cable_length = Decimal(str(data.get('wallbox_cable_length') or 0))
    wallbox_pv_surplus = str(data.get('wallbox_pv_surplus')).lower() in ['1', 'true', 'on']

    # Determine package
    if storage_kwh and storage_kwh > 0:
        package = 'pro'
    elif (desired_power and desired_power > 3) or inverter_class in ['5kva', '10kva'] or grid_type == 'TT':
        package = 'plus'
    else:
        package = 'basis'

    base_price = _pc({'basis': 'package_basis', 'plus': 'package_plus', 'pro': 'package_pro'}[package],
                     {'basis': Decimal('890.00'), 'plus': Decimal('1490.00'), 'pro': Decimal('2290.00')}[package])

    travel_cost = _infer_travel_cost(site_address)

    surcharges = Decimal('0.00')
    if grid_type == 'TT':
        surcharges += _pc('surcharge_tt_grid', Decimal('150.00'))
    if main_fuse and main_fuse > 35:
        surcharges += _pc('surcharge_selective_fuse', Decimal('220.00'))

    # WR Cable cost - variable based on power (added to surcharges)
    if distance and distance > 15:
        extra_distance = distance - Decimal('15')
        if desired_power <= 5:
            cable_price = _pc('cable_wr_up_to_5kw', Decimal('15.00'))
        elif desired_power <= 10:
            cable_price = _pc('cable_wr_5_to_10kw', Decimal('25.00'))
        else:
            cable_price = _pc('cable_wr_above_10kw', Decimal('35.00'))
        surcharges += extra_distance * cable_price

    material = Decimal('0.00')
    inverter_cost = Decimal('0.00')
    storage_cost = Decimal('0.00')

    if not own_components:
        inv_price_map = {'1kva': Decimal('800.00'), '3kva': Decimal('1200.00'), '5kva': Decimal('1800.00'), '10kva': Decimal('2800.00')}
        inv_price = inv_price_map.get(inverter_class, Decimal('0.00'))
        try:
            db_inv = Component.objects.filter(type='inverter').first()
            if db_inv:
                inv_price = db_inv.unit_price
        except Exception:
            pass
        inverter_cost += inv_price
        inverter_cost += _pc('material_ac_wiring', Decimal('180.00'))
        if package in ['plus', 'pro']:
            inverter_cost += _pc('material_spd', Decimal('320.00'))
            inverter_cost += _pc('material_meter_upgrade', Decimal('450.00'))
        if package == 'pro' and storage_kwh and storage_kwh > 0:
            storage_cost = storage_kwh * _pc('material_storage_kwh', Decimal('800.00'))

    # Wallbox cost calculation
    wallbox_cost = Decimal('0.00')
    if has_wallbox:
        # Base installation cost
        if wallbox_power == '4kw':
            wallbox_cost += _pc('wallbox_base_4kw', Decimal('890.00'))
        elif wallbox_power == '11kw':
            wallbox_cost += _pc('wallbox_base_11kw', Decimal('1290.00'))
        elif wallbox_power == '22kw':
            wallbox_cost += _pc('wallbox_base_22kw', Decimal('1690.00'))

        # Stand mount surcharge
        if wallbox_mount == 'stand':
            wallbox_cost += _pc('wallbox_stand_mount', Decimal('350.00'))

        # PV surplus charging (currently free)
        if wallbox_pv_surplus:
            wallbox_cost += _pc('wallbox_pv_surplus', Decimal('0.00'))

        # Cable cost
        if not wallbox_cable_installed and wallbox_cable_length > 0:
            if wallbox_power == '4kw':
                cable_price = _pc('cable_wb_4kw', Decimal('12.00'))
            elif wallbox_power == '11kw':
                cable_price = _pc('cable_wb_11kw', Decimal('20.00'))
            elif wallbox_power == '22kw':
                cable_price = _pc('cable_wb_22kw', Decimal('30.00'))
            else:
                cable_price = Decimal('0.00')
            wallbox_cost += wallbox_cable_length * cable_price

    material = inverter_cost + storage_cost + wallbox_cost

    discount = Decimal('0.00')
    if not own_components:
        try:
            disc = PriceConfig.objects.get(price_type='discount_complete_kit')
            discount = (base_price * disc.value) / Decimal('100') if disc.is_percentage else disc.value
        except PriceConfig.DoesNotExist:
            discount = (base_price * Decimal('0.15'))

    total = base_price + travel_cost + surcharges + material - discount

    return JsonResponse({
        'package': package,
        'basePrice': float(base_price),
        'travelCost': float(travel_cost),
        'surcharges': float(surcharges),
        'inverterCost': float(inverter_cost),
        'storageCost': float(storage_cost),
        'wallboxCost': float(wallbox_cost),
        'materialCost': float(material),
        'discount': float(discount),
        'total': float(total),
    })


@api_view(['POST'])
def create_precheck(request):
    return JsonResponse({'detail': 'not implemented'}, status=501)


@api_view(['POST'])
def approve_quote(request, pk):
    return JsonResponse({'detail': 'not implemented'}, status=501)


@api_view(['POST'])
def n8n_webhook(request):
    return JsonResponse({'detail': 'ok'})

