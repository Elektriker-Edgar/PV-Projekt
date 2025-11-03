"""
Management Command zum Laden von Beispiel-Komponenten für die Kalkulation
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.quotes.models import Component


class Command(BaseCommand):
    help = 'Lädt Beispiel-Komponenten für die Angebotskalkulation'

    def handle(self, *args, **options):
        # Wechselrichter
        inverters = [
            {
                'name': 'Sunny Boy 1.5',
                'type': 'inverter',
                'vendor': 'SMA',
                'sku': 'SB1.5-1VL-40',
                'unit_price': Decimal('650.00'),
                'datasheet_url': 'https://www.sma.de/produkte/wechselrichter/sunny-boy-15'
            },
            {
                'name': 'Sunny Boy 3.0',
                'type': 'inverter', 
                'vendor': 'SMA',
                'sku': 'SB3.0-1SP-US-41',
                'unit_price': Decimal('950.00'),
                'datasheet_url': 'https://www.sma.de/produkte/wechselrichter/sunny-boy-30'
            },
            {
                'name': 'Sunny Tripower 5.0',
                'type': 'inverter',
                'vendor': 'SMA', 
                'sku': 'STP5.0-3AV-40',
                'unit_price': Decimal('1450.00'),
                'datasheet_url': 'https://www.sma.de/produkte/wechselrichter/sunny-tripower-50'
            },
            {
                'name': 'Primo 3.0-1',
                'type': 'inverter',
                'vendor': 'Fronius',
                'sku': 'PRIMO3.0-1',
                'unit_price': Decimal('880.00'),
                'datasheet_url': 'https://www.fronius.com/de/solar-energy/installers-partners/technical-data/all-products/inverters/fronius-primo/fronius-primo-3-0-1'
            },
            {
                'name': 'SUN2000-3KTL-L1',
                'type': 'inverter',
                'vendor': 'Huawei',
                'sku': 'SUN2000-3KTL-L1',
                'unit_price': Decimal('750.00'),
                'datasheet_url': 'https://solar.huawei.com/eu/professionals/all-products/string-inverters/residential/sun2000-2ktl-5ktl-l1'
            }
        ]

        # Speichersysteme
        batteries = [
            {
                'name': 'Battery-Box Premium LVS 4.0',
                'type': 'battery',
                'vendor': 'BYD',
                'sku': 'B-BOX-LVS-4.0',
                'unit_price': Decimal('2800.00'),
                'datasheet_url': 'https://www.byd.com/eu/energy-storage/battery-box-premium-lvs'
            },
            {
                'name': 'US2000C',
                'type': 'battery',
                'vendor': 'Pylontech',
                'sku': 'US2000C',
                'unit_price': Decimal('1200.00'),
                'datasheet_url': 'https://www.pylontech.com.cn/pro_detail.aspx?id=121&cid=23'
            },
            {
                'name': 'STORION-S5',
                'type': 'battery',
                'vendor': 'Alpha ESS',
                'sku': 'STORION-S5',
                'unit_price': Decimal('3200.00'),
                'datasheet_url': 'https://www.alpha-ess.de/produkte/storion-s5'
            }
        ]

        # Überspannungsschutz
        spd_devices = [
            {
                'name': 'DEHNguard M TT 275',
                'type': 'spd',
                'vendor': 'DEHN',
                'sku': 'DGM-TT-275',
                'unit_price': Decimal('145.00'),
                'datasheet_url': 'https://www.dehn.de/de/produkte/blitzschutz-und-ueberspannungsschutz'
            },
            {
                'name': 'OVP Typ 2 AC 3P+N',
                'type': 'spd',
                'vendor': 'Phoenix Contact',
                'sku': 'VAL-MS-T2-3S+1FM',
                'unit_price': Decimal('180.00'),
                'datasheet_url': 'https://www.phoenixcontact.com/de-de/produkte/ueberspannungsschutz'
            }
        ]

        # Zählerplatz-Komponenten
        meter_components = [
            {
                'name': 'Zählerplatz 1-Feld modernisiert',
                'type': 'meter',
                'vendor': 'EDGARD', 
                'sku': 'ZP-MOD-1F',
                'unit_price': Decimal('380.00'),
                'datasheet_url': ''
            },
            {
                'name': 'Zählerplatz 2-Feld erweitert',
                'type': 'meter',
                'vendor': 'EDGARD',
                'sku': 'ZP-EXT-2F', 
                'unit_price': Decimal('520.00'),
                'datasheet_url': ''
            }
        ]

        # Kabel und Zubehör
        cables = [
            {
                'name': 'AC-Kabel 5x6mm² (pro Meter)',
                'type': 'cable',
                'vendor': 'Diverse',
                'sku': 'AC-CABLE-5x6',
                'unit_price': Decimal('8.50'),
                'datasheet_url': ''
            },
            {
                'name': 'DC-Kabel 4mm² (pro Meter)',
                'type': 'cable', 
                'vendor': 'Diverse',
                'sku': 'DC-CABLE-4',
                'unit_price': Decimal('3.20'),
                'datasheet_url': ''
            }
        ]

        # Alle Komponenten zusammenfassen
        all_components = inverters + batteries + spd_devices + meter_components + cables

        # Komponenten erstellen
        created_count = 0
        for comp_data in all_components:
            component, created = Component.objects.get_or_create(
                sku=comp_data['sku'],
                defaults=comp_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Erstellt: {component.vendor} {component.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ Existiert bereits: {component.vendor} {component.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n{created_count} neue Komponenten wurden erstellt.')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Insgesamt {Component.objects.count()} Komponenten in der Datenbank.')
        )