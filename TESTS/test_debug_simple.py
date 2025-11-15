"""
Einfacher Debug-Test - Nur die ersten 2 Schritte
"""

from playwright.sync_api import sync_playwright
import time

URL = "http://192.168.178.30:8025/precheck/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=1000)
    page = browser.new_page()

    print("Öffne Precheck...")
    page.goto(URL)
    time.sleep(2)

    print("\n=== SCHRITT 1 ===")

    # Prüfe welche Felder required sind
    required = page.locator("[required]").all()
    print(f"Gefundene Required-Felder: {len(required)}")
    for f in required:
        name = f.get_attribute("name") or f.get_attribute("id")
        print(f"  - {name}")

    print("\nFülle Pflichtfelder aus...")

    # Hauptsicherung (Required)
    page.fill("#main_fuse_ampere", "63")
    print("✅ main_fuse_ampere = 63")

    # Inverter Location (Required)
    page.select_option("#inverter_location", "basement")
    print("✅ inverter_location = basement")

    # Kabelweg (Required)
    page.fill("#distance_meter_to_inverter", "15")
    print("✅ distance_meter_to_inverter = 15")

    print("\nKlicke Weiter...")
    page.locator('.step-content.active button:has-text("Weiter")').click()
    time.sleep(2)

    print("\n=== SCHRITT 2 ===")

    # WR-Leistung (Required)
    page.fill("#desired_power_kw", "8.5")
    print("✅ desired_power_kw = 8.5")

    print("\nKlicke Preis berechnen...")
    page.click("button:has-text('Preis berechnen')")
    time.sleep(3)

    print("\n=== SCHRITT 3 (Preis) ===")
    print("Prüfe ob Preis angezeigt wird...")

    # Prüfe ob wir auf Schritt 3 sind
    if page.locator('[data-step="3"].active').count() > 0:
        print("✅ ERFOLG! Schritt 3 erreicht")
    else:
        print("❌ FEHLER! Nicht auf Schritt 3")

    input("\nDrücke Enter zum Beenden...")
    browser.close()
