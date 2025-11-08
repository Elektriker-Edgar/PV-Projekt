# Generated migration for Wallbox pricing configuration

from django.db import migrations
from decimal import Decimal


def seed_wallbox_pricing(apps, schema_editor):
    PriceConfig = apps.get_model('quotes', 'PriceConfig')

    # Wallbox Base Installation Preise
    wallbox_prices = [
        ('wallbox_base_4kw', Decimal('890.00'), False, 'Wallbox Installation <4kW'),
        ('wallbox_base_11kw', Decimal('1290.00'), False, 'Wallbox Installation 11kW'),
        ('wallbox_base_22kw', Decimal('1690.00'), False, 'Wallbox Installation 22kW'),
        ('wallbox_stand_mount', Decimal('350.00'), False, 'Wallbox Ständer-Montage Zuschlag'),
        ('wallbox_pv_surplus', Decimal('0.00'), False, 'PV-Überschussladen (aktuell kostenlos)'),
    ]

    # Kabelpreise Wechselrichter (abhängig von Leistung)
    wr_cable_prices = [
        ('cable_wr_up_to_5kw', Decimal('15.00'), False, 'WR-Kabel bis 5kW pro Meter'),
        ('cable_wr_5_to_10kw', Decimal('25.00'), False, 'WR-Kabel 5-10kW pro Meter'),
        ('cable_wr_above_10kw', Decimal('35.00'), False, 'WR-Kabel über 10kW pro Meter'),
    ]

    # Kabelpreise Wallbox (abhängig von Leistungsklasse)
    wb_cable_prices = [
        ('cable_wb_4kw', Decimal('12.00'), False, 'Wallbox-Kabel <4kW pro Meter'),
        ('cable_wb_11kw', Decimal('20.00'), False, 'Wallbox-Kabel 11kW pro Meter'),
        ('cable_wb_22kw', Decimal('30.00'), False, 'Wallbox-Kabel 22kW pro Meter'),
    ]

    all_prices = wallbox_prices + wr_cable_prices + wb_cable_prices

    for price_type, value, is_percentage, description in all_prices:
        PriceConfig.objects.get_or_create(
            price_type=price_type,
            defaults={
                'value': value,
                'is_percentage': is_percentage,
                'description': description,
            }
        )


def reverse_wallbox_pricing(apps, schema_editor):
    PriceConfig = apps.get_model('quotes', 'PriceConfig')

    price_types = [
        'wallbox_base_4kw',
        'wallbox_base_11kw',
        'wallbox_base_22kw',
        'wallbox_stand_mount',
        'wallbox_pv_surplus',
        'cable_wr_up_to_5kw',
        'cable_wr_5_to_10kw',
        'cable_wr_above_10kw',
        'cable_wb_4kw',
        'cable_wb_11kw',
        'cable_wb_22kw',
    ]

    PriceConfig.objects.filter(price_type__in=price_types).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0005_alter_priceconfig_price_type'),
    ]

    operations = [
        migrations.RunPython(seed_wallbox_pricing, reverse_wallbox_pricing),
    ]
