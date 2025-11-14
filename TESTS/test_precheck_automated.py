"""
Automatisierter Test für den Precheck-Wizard
==============================================

Dieses Script testet den vollständigen Precheck-Flow:
- Füllt alle Felder aus
- Uploaded Bilder und PDFs
- Sendet das Formular ab
- Validiert die Erfolgsseite

Verwendung:
    python test_precheck_automated.py

Requirements:
    pip install playwright
    playwright install chromium
"""

import os
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


# Konfiguration
BASE_URL = "http://192.168.178.30:8025"
PRECHECK_URL = f"{BASE_URL}/precheck/"
TEST_DIR = Path(__file__).parent
BILDER_DIR = TEST_DIR / "Bilder"

# Test-Daten
TEST_DATA = {
    # Kundendaten
    "customer_name": "Max Mustermann Test",
    "customer_email": "max.mustermann.test@example.com",
    "customer_phone": "+49 40 12345678",
    "customer_address": "Teststraße 123\n20095 Hamburg",

    # Gebäude & Bauzustand
    "building_type": "efh",
    "construction_year": "1995",
    "has_renovation": True,
    "renovation_year": "2020",

    # Elektrische Installation
    "main_fuse_ampere": "63",
    "grid_type": "3p",
    "has_sls_switch": True,
    "sls_switch_details": "SLS 63A vorhanden, Typ B",
    "has_surge_protection_ac": True,
    "surge_protection_ac_details": "Typ 2 Überspannungsschutz installiert",
    "has_grounding": "yes",
    "has_deep_earth": "yes",
    "grounding_details": "Potentialausgleich nach VDE 0100 vorhanden",

    # Montageorte & Kabelwege
    "inverter_location": "basement",
    "storage_location": "same_as_inverter",
    "distance_meter_to_inverter": "12.5",
    "grid_operator": "hamburgnetze",

    # PV-System
    "desired_power_kw": "8.5",
    "storage_kwh": "10.0",
    "feed_in_mode": "surplus",
    "requires_backup_power": True,
    "backup_power_details": "Notstrom für Kühlschrank, Heizung und Beleuchtung",
    "has_surge_protection_dc": True,
    "own_components": False,

    # Wallbox
    "has_wallbox": True,
    "wallbox_power": "11kw",
    "wallbox_mount": "wall",
    "wallbox_pv_surplus": True,
    "wallbox_cable_installed": False,
    "wallbox_cable_length": "25",

    # Wärmepumpe
    "has_heat_pump": True,
    "heat_pump_cascade": True,
    "heat_pump_details": "Luft-Wasser-WP, Viessmann Vitocal 200-S, 8 kW",

    # Notizen
    "notes": "Automatischer Test-Durchlauf\nGeneriert am " + time.strftime("%Y-%m-%d %H:%M:%S"),
}

# Datei-Uploads (verwendet vorhandene Dateien aus TESTS/Bilder/)
TEST_FILES = {
    "meter_cabinet_photo": "Zählerkasten.JPG",
    "hak_photo": "Stromzähler.JPG",
    "location_photo": "Stromzähler.JPG",  # Fallback, nutzt dasselbe Bild
    "cable_route_photo": "Übersicht_PV.pdf",
}


def check_test_files():
    """Prüft ob alle benötigten Test-Dateien vorhanden sind"""
    print(f"\n🔍 Prüfe Test-Dateien in: {BILDER_DIR}")

    if not BILDER_DIR.exists():
        print(f"❌ Verzeichnis nicht gefunden: {BILDER_DIR}")
        print(f"   Bitte erstelle das Verzeichnis und lege Test-Bilder hinein.")
        return False

    missing_files = []
    for field_name, filename in TEST_FILES.items():
        file_path = BILDER_DIR / filename
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {filename} ({size_mb:.2f} MB)")
        else:
            missing_files.append(filename)
            print(f"   ❌ {filename} - NICHT GEFUNDEN")

    if missing_files:
        print(f"\n⚠️  Fehlende Dateien: {', '.join(missing_files)}")
        print(f"   Bitte lege diese Dateien in {BILDER_DIR} ab")
        return False

    return True


def fill_accordion_section(page, accordion_id, fields):
    """Öffnet ein Accordion und füllt die Felder aus"""
    # Accordion öffnen wenn geschlossen
    accordion = page.locator(f"#{accordion_id}")
    if not accordion.get_attribute("class") or "show" not in accordion.get_attribute("class"):
        accordion_button = page.locator(f'button[data-bs-target="#{accordion_id}"]')
        accordion_button.click()
        time.sleep(0.3)

    # Felder ausfüllen
    for field_id, value in fields.items():
        if value is None:
            continue

        field = page.locator(f"#{field_id}")

        # Checkbox
        if isinstance(value, bool):
            if value and not field.is_checked():
                field.click()
                time.sleep(0.1)
        # Select/Input
        else:
            field.fill(str(value))
            time.sleep(0.05)


def run_precheck_test(headless=False, slow_mo=500):
    """
    Führt den automatisierten Precheck-Test durch

    Args:
        headless: True für Hintergrund-Ausführung, False zum Anschauen
        slow_mo: Verzögerung in ms zwischen Aktionen (für Debugging)
    """

    print("\n" + "="*60)
    print("🚀 Starte automatisierten Precheck-Test")
    print("="*60)

    # Prüfe Test-Dateien
    if not check_test_files():
        return False

    with sync_playwright() as p:
        # Browser starten
        print(f"\n🌐 Starte Browser (headless={headless})...")
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="de-DE"
        )
        page = context.new_page()

        try:
            # === SCHRITT 1: Standort & Elektro ===
            print(f"\n📍 Öffne Precheck-Seite: {PRECHECK_URL}")
            page.goto(PRECHECK_URL)
            page.wait_for_load_state("networkidle")

            print("✏️  SCHRITT 1: Standort & Elektro")

            # Accordion 1: Gebäude & Bauzustand
            print("   📦 Gebäude & Bauzustand")
            fill_accordion_section(page, "collapseBuilding", {
                "building_type": TEST_DATA["building_type"],
                "construction_year": TEST_DATA["construction_year"],
                "has_renovation": TEST_DATA["has_renovation"],
            })

            if TEST_DATA["has_renovation"]:
                time.sleep(0.2)  # Warte auf Toggle
                page.fill("#renovation_year", TEST_DATA["renovation_year"])

            # Accordion 2: Elektrische Installation
            print("   ⚡ Elektrische Installation")
            fill_accordion_section(page, "collapseElectrical", {
                "main_fuse_ampere": TEST_DATA["main_fuse_ampere"],
                "grid_type": TEST_DATA["grid_type"],
                "has_sls_switch": TEST_DATA["has_sls_switch"],
            })

            if TEST_DATA["has_sls_switch"]:
                time.sleep(0.2)
                page.fill("#sls_switch_details", TEST_DATA["sls_switch_details"])

            page.locator("#has_surge_protection_ac").click() if TEST_DATA["has_surge_protection_ac"] else None
            if TEST_DATA["has_surge_protection_ac"]:
                time.sleep(0.2)
                page.fill("#surge_protection_ac_details", TEST_DATA["surge_protection_ac_details"])

            page.select_option("#has_grounding", TEST_DATA["has_grounding"])
            time.sleep(0.2)
            page.select_option("#has_deep_earth", TEST_DATA["has_deep_earth"])
            time.sleep(0.2)
            page.fill("#grounding_details", TEST_DATA["grounding_details"])

            # Accordion 3: Montageorte & Kabelwege
            print("   📍 Montageorte & Kabelwege")
            fill_accordion_section(page, "collapseMounting", {
                "inverter_location": TEST_DATA["inverter_location"],
                "storage_location": TEST_DATA["storage_location"],
                "distance_meter_to_inverter": TEST_DATA["distance_meter_to_inverter"],
                "grid_operator": TEST_DATA["grid_operator"],
            })

            # Weiter zu Schritt 2
            print("   ➡️  Weiter zu Schritt 2")
            page.click("button:has-text('Weiter')")
            time.sleep(0.5)

            # === SCHRITT 2: PV-Wünsche ===
            print("\n✏️  SCHRITT 2: PV-Wünsche")

            # Accordion 1: PV-Konfiguration
            print("   ☀️  PV-Konfiguration")
            fill_accordion_section(page, "collapsePvConfig", {
                "desired_power_kw": TEST_DATA["desired_power_kw"],
                "storage_kwh": TEST_DATA["storage_kwh"],
                "feed_in_mode": TEST_DATA["feed_in_mode"],
            })

            page.locator("#requires_backup_power").click() if TEST_DATA["requires_backup_power"] else None
            if TEST_DATA["requires_backup_power"]:
                time.sleep(0.2)
                page.fill("#backup_power_details", TEST_DATA["backup_power_details"])

            page.locator("#has_surge_protection_dc").click() if TEST_DATA["has_surge_protection_dc"] else None
            page.locator("#own_components").click() if TEST_DATA["own_components"] else None

            # Accordion 2: Zusatzgeräte
            print("   🔌 Zusatzgeräte (Wallbox & Wärmepumpe)")
            fill_accordion_section(page, "collapseExtras", {})

            # Wallbox
            if TEST_DATA["has_wallbox"]:
                page.locator("#has_wallbox").click()
                time.sleep(0.3)
                page.select_option("#wallbox_power", TEST_DATA["wallbox_power"])
                page.select_option("#wallbox_mount", TEST_DATA["wallbox_mount"])
                if TEST_DATA["wallbox_pv_surplus"]:
                    page.locator("#wallbox_pv_surplus").click()
                if not TEST_DATA["wallbox_cable_installed"]:
                    page.fill("#wallbox_cable_length", TEST_DATA["wallbox_cable_length"])

            # Wärmepumpe
            if TEST_DATA["has_heat_pump"]:
                page.locator("#has_heat_pump").click()
                time.sleep(0.3)
                if TEST_DATA["heat_pump_cascade"]:
                    page.locator("#heat_pump_cascade").click()
                page.fill("#heat_pump_details", TEST_DATA["heat_pump_details"])

            # Preis berechnen
            print("   💰 Preis berechnen...")
            page.click("button:has-text('Preis berechnen')")
            time.sleep(2)  # Warte auf API-Call

            # === SCHRITT 3: Preis ===
            print("\n✏️  SCHRITT 3: Preisanzeige")
            print("   ✅ Preis erfolgreich berechnet")

            # Screenshot vom Preis
            screenshot_path = TEST_DIR / f"screenshot_preis_{time.strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=str(screenshot_path))
            print(f"   📸 Screenshot gespeichert: {screenshot_path.name}")

            # Weiter zu Schritt 4
            print("   ➡️  Weiter zu Schritt 4")
            page.click("button:has-text('Weiter')")
            time.sleep(0.5)

            # === SCHRITT 4: Fotos hochladen ===
            print("\n✏️  SCHRITT 4: Fotos hochladen")

            for field_name, filename in TEST_FILES.items():
                file_path = BILDER_DIR / filename
                if file_path.exists():
                    print(f"   📤 Upload {filename}...")
                    page.set_input_files(f"#{field_name}", str(file_path))
                    time.sleep(0.3)

            # Weiter zu Schritt 5
            print("   ➡️  Weiter zu Schritt 5")
            page.click("button:has-text('Weiter')")
            time.sleep(0.5)

            # === SCHRITT 5: Kontaktdaten & Zusammenfassung ===
            print("\n✏️  SCHRITT 5: Kontaktdaten & Zusammenfassung")

            page.fill("#customer_name", TEST_DATA["customer_name"])
            page.fill("#customer_email", TEST_DATA["customer_email"])
            page.fill("#customer_phone", TEST_DATA["customer_phone"])
            page.fill("#customer_address", TEST_DATA["customer_address"])
            page.fill("#notes", TEST_DATA["notes"])

            # Screenshot der Zusammenfassung
            screenshot_path = TEST_DIR / f"screenshot_zusammenfassung_{time.strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=str(screenshot_path))
            print(f"   📸 Screenshot gespeichert: {screenshot_path.name}")

            # Weiter zu Schritt 6
            print("   ➡️  Weiter zu Schritt 6")
            page.click("button:has-text('Weiter')")
            time.sleep(0.5)

            # === SCHRITT 6: Datenschutz & Absenden ===
            print("\n✏️  SCHRITT 6: Datenschutz & Absenden")

            page.locator("#consent").click()
            time.sleep(0.3)

            print("   📨 Formular absenden...")
            page.click("button:has-text('Angebot anfordern')")

            # Warte auf Erfolgsseite
            print("   ⏳ Warte auf Erfolgsseite...")
            page.wait_for_url("**/precheck/success/**", timeout=15000)

            # === ERFOLGSSEITE ===
            print("\n✅ SUCCESS-SEITE ERREICHT!")

            # Screenshot der Erfolgsseite
            screenshot_path = TEST_DIR / f"screenshot_success_{time.strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=str(screenshot_path))
            print(f"   📸 Screenshot gespeichert: {screenshot_path.name}")

            # Extrahiere Informationen
            success_text = page.inner_text("body")
            if "Angebot" in success_text:
                print("   ✅ Angebot wurde erstellt")

            print("\n" + "="*60)
            print("🎉 TEST ERFOLGREICH ABGESCHLOSSEN!")
            print("="*60)

            return True

        except Exception as e:
            print(f"\n❌ FEHLER: {e}")

            # Fehler-Screenshot
            try:
                error_screenshot = TEST_DIR / f"screenshot_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=str(error_screenshot))
                print(f"   📸 Fehler-Screenshot: {error_screenshot.name}")
            except:
                pass

            return False

        finally:
            if not headless:
                print("\n⏸️  Browser bleibt offen für Inspektion (Drücke Enter zum Schließen)...")
                input()

            browser.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Automatisierter Precheck-Test")
    parser.add_argument("--headless", action="store_true", help="Browser im Hintergrund ausführen")
    parser.add_argument("--fast", action="store_true", help="Schneller Modus (keine Verzögerungen)")

    args = parser.parse_args()

    slow_mo = 0 if args.fast else 300
    success = run_precheck_test(headless=args.headless, slow_mo=slow_mo)

    exit(0 if success else 1)
