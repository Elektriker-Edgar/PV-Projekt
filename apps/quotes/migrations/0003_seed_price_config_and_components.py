from django.db import migrations
from decimal import Decimal


def seed_prices_and_components(apps, schema_editor):
    PriceConfig = apps.get_model('quotes', 'PriceConfig')
    Component = apps.get_model('quotes', 'Component')

    price_rows = [
        # Packages
        ('package_basis', Decimal('890.00'), False, 'Basis-Paket'),
        ('package_plus', Decimal('1490.00'), False, 'Plus-Paket'),
        ('package_pro', Decimal('2290.00'), False, 'Pro-Paket'),
        # Travel
        ('travel_zone_0', Decimal('0.00'), False, 'Anfahrt Hamburg'),
        ('travel_zone_30', Decimal('50.00'), False, 'Anfahrt bis 30km'),
        ('travel_zone_60', Decimal('95.00'), False, 'Anfahrt bis 60km'),
        # Surcharges
        ('surcharge_tt_grid', Decimal('150.00'), False, 'TT-Netz Zuschlag'),
        ('surcharge_selective_fuse', Decimal('220.00'), False, 'Selektive Vorsicherung'),
        ('surcharge_cable_meter', Decimal('25.00'), False, 'Zuschlag je zusätzl. Meter (>15m)'),
        # Material
        ('material_ac_wiring', Decimal('180.00'), False, 'AC-Verkabelung'),
        ('material_spd', Decimal('320.00'), False, 'Überspannungsschutz (SPD)'),
        ('material_meter_upgrade', Decimal('450.00'), False, 'Zählerplatz-Ertüchtigung'),
        ('material_storage_kwh', Decimal('800.00'), False, 'Speicher pro kWh'),
        # Discount
        ('discount_complete_kit', Decimal('15.00'), True, 'Komplett-Kit Rabatt %'),
    ]

    for price_type, value, is_percentage, desc in price_rows:
        PriceConfig.objects.update_or_create(
            price_type=price_type,
            defaults={
                'value': value,
                'is_percentage': is_percentage,
                'description': desc,
            },
        )

    components = [
        {
            'name': 'Wechselrichter 5 kVA',
            'type': 'inverter',
            'vendor': 'DemoVendor',
            'sku': 'INV-5K-DEMO',
            'unit_price': Decimal('1800.00'),
        },
        {
            'name': 'Überspannungsschutz (SPD)',
            'type': 'spd',
            'vendor': 'DemoVendor',
            'sku': 'SPD-AC-DEMO',
            'unit_price': Decimal('320.00'),
        },
        {
            'name': 'Zählerplatz-Upgrade',
            'type': 'meter',
            'vendor': 'DemoVendor',
            'sku': 'METER-UP-DEM',
            'unit_price': Decimal('450.00'),
        },
    ]

    for c in components:
        Component.objects.update_or_create(
            sku=c['sku'],
            defaults={
                'name': c['name'],
                'type': c['type'],
                'vendor': c['vendor'],
                'unit_price': c['unit_price'],
            },
        )


def unseed_prices_and_components(apps, schema_editor):
    Component = apps.get_model('quotes', 'Component')
    Component.objects.filter(sku__in=['INV-5K-DEMO', 'SPD-AC-DEMO', 'METER-UP-DEM']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('quotes', '0002_priceconfig'),
    ]

    operations = [
        migrations.RunPython(seed_prices_and_components, unseed_prices_and_components),
    ]

