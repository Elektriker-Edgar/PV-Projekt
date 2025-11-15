"""
SCHNELLER PRECHECK-TEST - NUR PFLICHTFELDER
============================================
Füllt nur die absolut notwendigen Felder aus und sendet ab.
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

# Config
URL = "http://192.168.178.30:8025/precheck/"
BILDER = Path(__file__).parent / "Bilder"

print("\n" + "="*60)
print("🚀 SCHNELLER PRECHECK-TEST")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page()

    print(f"\n📍 Öffne: {URL}")
    page.goto(URL)
    page.wait_for_load_state("networkidle")

    # === SCHRITT 1 ===
    print("\n📝 SCHRITT 1: Standort & Elektro")
    page.fill("#main_fuse_ampere", "63")
    page.select_option("#inverter_location", "basement")
    page.fill("#distance_meter_to_inverter", "15")
    print("   ✅ Pflichtfelder ausgefüllt")

    page.locator('.step-content.active button:has-text("Weiter")').click()
    time.sleep(1)

    # === SCHRITT 2 ===
    print("\n📝 SCHRITT 2: PV-Wünsche")
    page.fill("#desired_power_kw", "8.5")
    print("   ✅ Pflichtfelder ausgefüllt")

    page.click("button:has-text('Preis berechnen')")
    time.sleep(3)

    # === SCHRITT 3 ===
    print("\n💰 SCHRITT 3: Preis")
    print("   ✅ Preis berechnet")

    page.locator('.step-content.active button:has-text("Weiter")').click()
    time.sleep(1)

    # === SCHRITT 4 ===
    print("\n📸 SCHRITT 4: Fotos (optional - überspringe)")
    page.locator('.step-content.active button:has-text("Weiter")').click()
    time.sleep(1)

    # === SCHRITT 5 ===
    print("\n👤 SCHRITT 5: Kontaktdaten")
    page.fill("#customer_name", "Test User")
    page.fill("#customer_email", "test@example.com")
    page.fill("#customer_phone", "+49 40 12345678")
    print("   ✅ Kontaktdaten ausgefüllt")

    page.locator('.step-content.active button:has-text("Weiter")').click()
    time.sleep(1)

    # === SCHRITT 6 ===
    print("\n✅ SCHRITT 6: Datenschutz & Absenden")
    page.locator("#consent").click()
    time.sleep(0.5)

    print("\n📨 SENDE FORMULAR AB...")
    page.click("button:has-text('Angebot anfordern')")

    # Warte auf Erfolg ODER Fehler
    time.sleep(3)

    current_url = page.url
    print(f"\n🔍 Aktuelle URL: {current_url}")

    if "success" in current_url:
        print("\n🎉 ERFOLG! Precheck wurde erfolgreich abgesendet!")
        page.screenshot(path="screenshot_success.png")
    else:
        print("\n❌ FEHLER! Formular wurde zurückgewiesen")

        # Zeige Fehlermeldungen
        errors = page.locator(".invalid-feedback:visible, .alert-danger:visible").all()
        if errors:
            print("\n🔴 Gefundene Fehler:")
            for err in errors:
                print(f"   - {err.inner_text()}")

        page.screenshot(path="screenshot_fehler.png")

    input("\n⏸️  Drücke Enter zum Beenden...")
    browser.close()

print("\n" + "="*60)
