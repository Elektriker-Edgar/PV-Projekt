#!/usr/bin/env python
"""
Erstellt Beispieldaten für die PV-Service Anwendung
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pv_service.settings')
django.setup()

from apps.core.models import User
from apps.customers.models import Customer, Site
from apps.quotes.models import Component, Precheck


def create_components():
    """Erstellt Component-Datensätze für Preisberechnung"""
    components = [
        # Wechselrichter
        {
            'name': 'SolarEdge SE1000',
            'type': 'inverter',
            'vendor': 'SolarEdge',
            'sku': 'SE1000-1PH',
            'unit_price': Decimal('800.00'),
            'datasheet_url': 'https://solaredge.com/se1000'
        },
        {
            'name': 'SolarEdge SE3000H',
            'type': 'inverter', 
            'vendor': 'SolarEdge',
            'sku': 'SE3000H-1PH',
            'unit_price': Decimal('1200.00'),
            'datasheet_url': 'https://solaredge.com/se3000h'
        },
        {
            'name': 'SolarEdge SE5000H',
            'type': 'inverter',
            'vendor': 'SolarEdge',
            'sku': 'SE5000H-1PH', 
            'unit_price': Decimal('1800.00'),
            'datasheet_url': 'https://solaredge.com/se5000h'
        },
        {
            'name': 'SolarEdge SE10000H',
            'type': 'inverter',
            'vendor': 'SolarEdge',
            'sku': 'SE10000H-3PH',
            'unit_price': Decimal('2800.00'),
            'datasheet_url': 'https://solaredge.com/se10000h'
        },
        
        # Speichersysteme
        {
            'name': 'BYD Battery-Box Premium LVS',
            'type': 'battery',
            'vendor': 'BYD',
            'sku': 'B-BOX-LVS-4.0',
            'unit_price': Decimal('3200.00'),
            'datasheet_url': 'https://byd.com/battery-box'
        },
        {
            'name': 'Pylontech US2000C',
            'type': 'battery',
            'vendor': 'Pylontech',
            'sku': 'US2000C-48V',
            'unit_price': Decimal('1600.00'),
            'datasheet_url': 'https://pylontech.com/us2000c'
        },
        
        # Überspannungsschutz
        {
            'name': 'Phoenix Contact VAL-MS-T1/T2',
            'type': 'spd',
            'vendor': 'Phoenix Contact',
            'sku': 'VAL-MS-T1-T2-335-FM',
            'unit_price': Decimal('320.00'),
            'datasheet_url': 'https://phoenixcontact.com/val-ms'
        },
        {
            'name': 'Dehn DG M TT 255',
            'type': 'spd',
            'vendor': 'Dehn',
            'sku': 'DG-M-TT-255',
            'unit_price': Decimal('280.00'),
            'datasheet_url': 'https://dehn.de/dg-m-tt'
        },
        
        # Zählerplatz
        {
            'name': 'Hager Zählerplatz ZB33SN',
            'type': 'meter',
            'vendor': 'Hager',
            'sku': 'ZB33SN',
            'unit_price': Decimal('450.00'),
            'datasheet_url': 'https://hager.com/zb33sn'
        },
        
        # Kabel
        {
            'name': 'NYM-J 5x16 mm²',
            'type': 'cable',
            'vendor': 'Lapp',
            'sku': 'NYM-J-5X16',
            'unit_price': Decimal('12.50'),
            'datasheet_url': 'https://lapp.com/nym-j'
        },
        {
            'name': 'AC-Anschlusskabel Set',
            'type': 'cable',
            'vendor': 'EDGARD',
            'sku': 'AC-CABLE-SET-01',
            'unit_price': Decimal('180.00'),
            'datasheet_url': ''
        }
    ]
    
    created_count = 0
    for comp_data in components:
        component, created = Component.objects.get_or_create(
            sku=comp_data['sku'],
            defaults=comp_data
        )
        if created:
            created_count += 1
            print(f"✓ Component erstellt: {component}")
        else:
            print(f"- Component existiert bereits: {component}")
    
    print(f"\n{created_count} neue Components erstellt.")
    return Component.objects.all()


def create_sample_customer():
    """Erstellt Beispielkunde mit Site"""
    customer_data = {
        'name': 'Max Mustermann',
        'email': 'max.mustermann@example.com',
        'phone': '+49 40 123456789',
        'customer_type': 'private',
        'address': 'Musterstraße 123\n20095 Hamburg',
        'consent_timestamp': datetime.now(),
        'consent_ip': '192.168.178.30'
    }
    
    customer, created = Customer.objects.get_or_create(
        email=customer_data['email'],
        defaults=customer_data
    )
    
    if created:
        print(f"✓ Customer erstellt: {customer}")
    else:
        print(f"- Customer existiert bereits: {customer}")
    
    # Site für Customer
    site_data = {
        'customer': customer,
        'address': 'Musterstraße 123\n20095 Hamburg',
        'building_type': 'efh',
        'construction_year': 2010,
        'main_fuse_ampere': 40,
        'grid_type': 'TN-S',
        'distance_meter_to_hak': Decimal('15.5')
    }
    
    site, created = Site.objects.get_or_create(
        customer=customer,
        defaults=site_data
    )
    
    if created:
        print(f"✓ Site erstellt: {site}")
    else:
        print(f"- Site existiert bereits: {site}")
    
    return customer, site


def create_sample_precheck(site):
    """Erstellt Beispiel-Vorprüfung"""
    precheck_data = {
        'site': site,
        'desired_power_kw': Decimal('5.0'),
        'inverter_class': '5kva',
        'storage_kwh': Decimal('10.0'),
        'own_components': False,
        'component_files': '[]',
        'preferred_timeframes': '["vormittags", "nachmittags"]',
        'notes': 'Beispiel-Vorprüfung für Testing'
    }
    
    precheck, created = Precheck.objects.get_or_create(
        site=site,
        defaults=precheck_data
    )
    
    if created:
        print(f"✓ Precheck erstellt: {precheck}")
    else:
        print(f"- Precheck existiert bereits: {precheck}")
    
    return precheck


def main():
    """Hauptfunktion"""
    print("=== Erstelle Beispieldaten für PV-Service ===\n")
    
    # 1. Components
    print("1. Erstelle Components...")
    components = create_components()
    
    # 2. Customer & Site
    print("\n2. Erstelle Customer & Site...")
    customer, site = create_sample_customer()
    
    # 3. Precheck
    print("\n3. Erstelle Precheck...")
    precheck = create_sample_precheck(site)
    
    print("\n=== Zusammenfassung ===")
    print(f"Components: {Component.objects.count()}")
    print(f"Customers: {Customer.objects.count()}")
    print(f"Sites: {Site.objects.count()}")
    print(f"Prechecks: {Precheck.objects.count()}")
    
    print(f"\n✅ Alle Beispieldaten erstellt!")
    print(f"🌐 Test unter: http://192.168.178.30:8020/precheck/")
    print(f"⚙️  Admin: http://192.168.178.30:8020/admin/")


if __name__ == '__main__':
    main()