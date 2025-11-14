"""
Django-basierter Precheck-Test (ohne Browser)
==============================================

Testet den Precheck direkt über Django's Test-Client.
Schneller als Browser-Automatisierung, aber testet kein JavaScript.

Verwendung:
    python manage.py test TESTS.test_precheck_django

Oder direkt:
    cd E:\ANPR\PV-Service
    python TESTS\test_precheck_django.py
"""

import os
import sys
from pathlib import Path
from decimal import Decimal
from io import BytesIO
from PIL import Image

# Django Setup
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edgard_site.settings')

import django
django.setup()

from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.quotes.models import Precheck
from apps.customers.models import Customer, Site


class PrecheckSubmissionTest(TestCase):
    """Test-Suite für Precheck-Formular Submission"""

    def setUp(self):
        """Test-Vorbereitung"""
        self.client = Client()
        self.bilder_dir = project_root / "TESTS" / "Bilder"

    def create_test_image(self, filename="test.jpg", size=(800, 600)):
        """Erstellt ein Test-Bild in-memory"""
        image = Image.new('RGB', size, color='red')
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)
        return SimpleUploadedFile(
            filename,
            buffer.read(),
            content_type='image/jpeg'
        )

    def create_test_pdf(self, filename="test.pdf"):
        """Erstellt ein Test-PDF in-memory"""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"
        return SimpleUploadedFile(
            filename,
            pdf_content,
            content_type='application/pdf'
        )

    def get_test_files(self):
        """Lädt echte Test-Dateien aus TESTS/Bilder/ oder erstellt Mock-Dateien"""
        files = {}

        # Verwende vorhandene Dateien aus TESTS/Bilder/
        test_files = {
            'meter_cabinet_photo': 'Zählerkasten.JPG',
            'hak_photo': 'Stromzähler.JPG',
            'location_photo': 'Stromzähler.JPG',
            'cable_route_photo': 'Übersicht_PV.pdf',
        }

        for field_name, filename in test_files.items():
            file_path = self.bilder_dir / filename
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content_type = 'application/pdf' if filename.endswith('.pdf') else 'image/jpeg'
                    files[field_name] = SimpleUploadedFile(filename, content, content_type=content_type)
            else:
                # Fallback: Erstelle Mock-Datei
                if filename.endswith('.pdf'):
                    files[field_name] = self.create_test_pdf(filename)
                else:
                    files[field_name] = self.create_test_image(filename)

        return files

    def test_precheck_complete_submission(self):
        """Test: Vollständiges Precheck-Formular mit allen Feldern"""

        print("\n" + "="*60)
        print("🧪 Test: Vollständiges Precheck-Formular")
        print("="*60)

        # Test-Daten
        data = {
            # Kundendaten
            'customer_name': 'Django Test User',
            'customer_email': 'django.test@example.com',
            'customer_phone': '+49 40 98765432',
            'customer_address': 'Django-Teststraße 456\n20095 Hamburg',
            'customer_type': 'private',
            'consent': True,

            # Gebäude & Bauzustand
            'building_type': 'efh',
            'construction_year': 1998,
            'has_renovation': True,
            'renovation_year': 2022,

            # Elektrische Installation
            'main_fuse_ampere': 63,
            'grid_type': '3p',
            'has_sls_switch': True,
            'sls_switch_details': 'SLS 63A Typ B vorhanden',
            'has_surge_protection_ac': True,
            'surge_protection_ac_details': 'Typ 2 Überspannungsschutz',
            'has_grounding': 'yes',
            'has_deep_earth': 'yes',
            'grounding_details': 'Potentialausgleich nach VDE',

            # Montageorte & Kabelwege
            'inverter_location': 'Keller',
            'storage_location': 'Keller',
            'distance_meter_to_inverter': '15.0',
            'grid_operator': 'Hamburg Netz GmbH',

            # PV-System
            'desired_power_kw': '10.0',
            'storage_kwh': '12.0',
            'feed_in_mode': 'surplus',
            'requires_backup_power': True,
            'backup_power_details': 'Notstrom für kritische Verbraucher',
            'has_surge_protection_dc': True,
            'own_components': False,

            # Wallbox
            'has_wallbox': True,
            'wallbox_power': '11kw',
            'wallbox_mount': 'wall',
            'wallbox_pv_surplus': True,
            'wallbox_cable_installed': False,
            'wallbox_cable_length': '20',

            # Wärmepumpe
            'has_heat_pump': True,
            'heat_pump_cascade': True,
            'heat_pump_details': 'Viessmann Vitocal 200-S, 8 kW',

            # Notizen
            'notes': 'Django Test-Durchlauf',
        }

        # Dateien vorbereiten
        files = self.get_test_files()
        data.update(files)

        print("\n📤 Sende Precheck-Formular...")

        # Formular absenden
        response = self.client.post('/precheck/', data, follow=True)

        # Assertions
        print(f"   Status Code: {response.status_code}")
        self.assertEqual(response.status_code, 200, "Status Code sollte 200 sein")

        # Prüfe ob Success-Seite erreicht wurde
        self.assertContains(response, 'success', msg_prefix="Sollte Success-Seite enthalten")

        # Prüfe Datenbank
        precheck_count = Precheck.objects.count()
        customer_count = Customer.objects.count()
        site_count = Site.objects.count()

        print(f"   ✅ Prechecks erstellt: {precheck_count}")
        print(f"   ✅ Customers erstellt: {customer_count}")
        print(f"   ✅ Sites erstellt: {site_count}")

        self.assertEqual(precheck_count, 1, "Ein Precheck sollte erstellt worden sein")
        self.assertEqual(customer_count, 1, "Ein Customer sollte erstellt worden sein")
        self.assertEqual(site_count, 1, "Eine Site sollte erstellt worden sein")

        # Prüfe erstellte Objekte
        precheck = Precheck.objects.first()
        customer = Customer.objects.first()
        site = Site.objects.first()

        print(f"\n📋 Erstellte Objekte:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Site: {site.address}")
        print(f"   Precheck-ID: {precheck.id}")

        # Validiere wichtige Felder
        self.assertEqual(customer.email, 'django.test@example.com')
        self.assertEqual(precheck.building_type, 'efh')
        self.assertEqual(precheck.desired_power_kw, Decimal('10.0'))
        self.assertEqual(precheck.storage_kwh, Decimal('12.0'))
        self.assertTrue(precheck.has_wallbox)
        self.assertTrue(precheck.has_heat_pump)
        self.assertTrue(precheck.wallbox_pv_surplus)
        self.assertEqual(precheck.feed_in_mode, 'surplus')

        print("\n✅ Alle Assertions erfolgreich!")
        print("="*60)

    def test_precheck_minimal_submission(self):
        """Test: Minimales Precheck-Formular (nur Pflichtfelder)"""

        print("\n" + "="*60)
        print("🧪 Test: Minimales Precheck-Formular")
        print("="*60)

        data = {
            # Pflichtfelder
            'customer_name': 'Minimal Test',
            'customer_email': 'minimal@example.com',
            'consent': True,
            'main_fuse_ampere': 35,
            'distance_meter_to_inverter': '5.0',
            'inverter_location': 'basement',
            'desired_power_kw': '5.0',
        }

        print("\n📤 Sende minimales Formular...")
        response = self.client.post('/precheck/', data, follow=True)

        print(f"   Status Code: {response.status_code}")
        self.assertEqual(response.status_code, 200)

        # Prüfe Datenbank
        precheck_count = Precheck.objects.count()
        print(f"   ✅ Prechecks erstellt: {precheck_count}")
        self.assertEqual(precheck_count, 1)

        precheck = Precheck.objects.first()
        print(f"   ✅ Precheck-ID: {precheck.id}")
        print(f"   ✅ WR-Leistung: {precheck.desired_power_kw} kW")

        # Validiere dass optionale Felder leer sind
        self.assertFalse(precheck.has_wallbox)
        self.assertFalse(precheck.has_heat_pump)
        self.assertEqual(precheck.building_type, '')
        self.assertIsNone(precheck.storage_kwh)

        print("\n✅ Minimales Formular erfolgreich!")
        print("="*60)


def run_tests():
    """Führt die Tests direkt aus (ohne manage.py)"""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)

    print("\n🚀 Starte Django-Tests für Precheck...")
    failures = test_runner.run_tests(["TESTS.test_precheck_django"])

    if failures == 0:
        print("\n🎉 ALLE TESTS ERFOLGREICH!")
    else:
        print(f"\n❌ {failures} TEST(S) FEHLGESCHLAGEN")

    return failures


if __name__ == '__main__':
    # Direkte Ausführung
    run_tests()
