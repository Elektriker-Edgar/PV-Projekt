"""
Script zum Erstellen von Test-Daten für den Produktkatalog
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edgard_site.settings')
django.setup()

from apps.quotes.models import ProductCategory, Product
from decimal import Decimal

print("Erstelle Produktkategorien...")

# Kategorien erstellen
categories_data = [
    {"name": "Precheck-Artikel", "description": "Artikel für Precheck-Kalkulation", "sort_order": 1},
    {"name": "Wechselrichter", "description": "Wechselrichter für PV-Anlagen", "sort_order": 2},
    {"name": "Speicher", "description": "Batteriespeicher-Systeme", "sort_order": 3},
    {"name": "Installationsmaterial", "description": "Material für die Installation", "sort_order": 4},
    {"name": "Kabel", "description": "DC- und AC-Kabel", "sort_order": 5},
    {"name": "Dienstleistungen", "description": "Montage, Planung und Beratung", "sort_order": 6},
    {"name": "Zubehör", "description": "Diverses Zubehör", "sort_order": 7},
]

categories = {}
for cat_data in categories_data:
    cat, created = ProductCategory.objects.get_or_create(
        name=cat_data["name"],
        defaults={
            "description": cat_data["description"],
            "sort_order": cat_data["sort_order"]
        }
    )
    categories[cat_data["name"]] = cat
    status = "[+] Erstellt" if created else "[o] Existiert bereits"
    print(f"  {status}: {cat.name}")

print("\nErstelle Produkte...")

# Precheck-Artikel
precheck_products = [
    {"sku": "PRECHK-BASE", "name": "Basis-Paket", "unit": "package", "purchase": 150, "sales": 299, "vat": 0.19},
    {"sku": "PRECHK-PLUS", "name": "Plus-Paket", "unit": "package", "purchase": 250, "sales": 499, "vat": 0.19},
    {"sku": "PRECHK-PRO", "name": "Pro-Paket", "unit": "package", "purchase": 400, "sales": 799, "vat": 0.19},
    {"sku": "TRAVEL-0", "name": "Anfahrt Zone 0 (Hamburg)", "unit": "lump_sum", "purchase": 20, "sales": 50, "vat": 0.19},
    {"sku": "TRAVEL-30", "name": "Anfahrt Zone 30 (bis 30km)", "unit": "lump_sum", "purchase": 30, "sales": 75, "vat": 0.19},
    {"sku": "TRAVEL-60", "name": "Anfahrt Zone 60 (bis 60km)", "unit": "lump_sum", "purchase": 50, "sales": 125, "vat": 0.19},
]

for p_data in precheck_products:
    product, created = Product.objects.get_or_create(
        sku=p_data["sku"],
        defaults={
            "category": categories["Precheck-Artikel"],
            "name": p_data["name"],
            "unit": p_data["unit"],
            "purchase_price_net": Decimal(str(p_data["purchase"])),
            "sales_price_net": Decimal(str(p_data["sales"])),
            "vat_rate": Decimal(str(p_data["vat"])),
        }
    )
    status = "[+]" if created else "[o]"
    print(f"  {status} {product.sku} - {product.name}")

# Wechselrichter
inverter_products = [
    {"sku": "INV-FRONIUS-5", "name": "Fronius Symo 5.0-3-M", "manufacturer": "Fronius", "purchase": 800, "sales": 1200, "vat": 0.19},
    {"sku": "INV-FRONIUS-10", "name": "Fronius Symo 10.0-3-M", "manufacturer": "Fronius", "purchase": 1200, "sales": 1800, "vat": 0.19},
    {"sku": "INV-KOSTAL-8", "name": "KOSTAL PLENTICORE plus 8.5", "manufacturer": "KOSTAL", "purchase": 900, "sales": 1400, "vat": 0.19},
    {"sku": "INV-SMA-6", "name": "SMA Sunny Tripower 6.0", "manufacturer": "SMA", "purchase": 850, "sales": 1300, "vat": 0.19},
]

for p_data in inverter_products:
    product, created = Product.objects.get_or_create(
        sku=p_data["sku"],
        defaults={
            "category": categories["Wechselrichter"],
            "name": p_data["name"],
            "unit": "piece",
            "manufacturer": p_data["manufacturer"],
            "purchase_price_net": Decimal(str(p_data["purchase"])),
            "sales_price_net": Decimal(str(p_data["sales"])),
            "vat_rate": Decimal(str(p_data["vat"])),
            "stock_quantity": 5,
            "min_stock_level": 2,
        }
    )
    status = "[+]" if created else "[o]"
    print(f"  {status} {product.sku} - {product.name}")

# Speicher
battery_products = [
    {"sku": "BAT-BYD-5", "name": "BYD Battery-Box Premium HVS 5.1", "manufacturer": "BYD", "purchase": 2500, "sales": 3800, "vat": 0.19},
    {"sku": "BAT-BYD-10", "name": "BYD Battery-Box Premium HVS 10.2", "manufacturer": "BYD", "purchase": 4500, "sales": 6800, "vat": 0.19},
    {"sku": "BAT-VARTA-6", "name": "VARTA pulse neo 6.5", "manufacturer": "VARTA", "purchase": 2800, "sales": 4200, "vat": 0.19},
]

for p_data in battery_products:
    product, created = Product.objects.get_or_create(
        sku=p_data["sku"],
        defaults={
            "category": categories["Speicher"],
            "name": p_data["name"],
            "unit": "piece",
            "manufacturer": p_data["manufacturer"],
            "purchase_price_net": Decimal(str(p_data["purchase"])),
            "sales_price_net": Decimal(str(p_data["sales"])),
            "vat_rate": Decimal(str(p_data["vat"])),
            "stock_quantity": 3,
            "min_stock_level": 1,
        }
    )
    status = "[+]" if created else "[o]"
    print(f"  {status} {product.sku} - {product.name}")

# Kabel
cable_products = [
    {"sku": "CABLE-DC-6MM", "name": "DC-Kabel 6mm² (Solar)", "purchase": 2.50, "sales": 5.00, "vat": 0.19},
    {"sku": "CABLE-DC-4MM", "name": "DC-Kabel 4mm² (Solar)", "purchase": 1.80, "sales": 3.80, "vat": 0.19},
    {"sku": "CABLE-AC-5G6", "name": "AC-Kabel NYM-J 5x6mm²", "purchase": 4.50, "sales": 8.50, "vat": 0.19},
    {"sku": "CABLE-AC-5G25", "name": "AC-Kabel NYM-J 5x2.5mm²", "purchase": 2.80, "sales": 5.50, "vat": 0.19},
]

for p_data in cable_products:
    product, created = Product.objects.get_or_create(
        sku=p_data["sku"],
        defaults={
            "category": categories["Kabel"],
            "name": p_data["name"],
            "unit": "meter",
            "purchase_price_net": Decimal(str(p_data["purchase"])),
            "sales_price_net": Decimal(str(p_data["sales"])),
            "vat_rate": Decimal(str(p_data["vat"])),
            "stock_quantity": 250,
            "min_stock_level": 50,
        }
    )
    status = "[+]" if created else "[o]"
    print(f"  {status} {product.sku} - {product.name}")

# Installationsmaterial
install_products = [
    {"sku": "INST-SPD-T1T2", "name": "Überspannungsschutz Typ 1+2", "purchase": 120, "sales": 220, "vat": 0.19},
    {"sku": "INST-METER-UPG", "name": "Zählerplatz-Ertüchtigung", "purchase": 200, "sales": 380, "vat": 0.19},
    {"sku": "INST-AC-WIRE", "name": "AC-Verkabelung Set", "purchase": 150, "sales": 280, "vat": 0.19},
    {"sku": "INST-MOUNT-KIT", "name": "Montage-Set Dachhaken", "purchase": 80, "sales": 150, "vat": 0.19},
]

for p_data in install_products:
    product, created = Product.objects.get_or_create(
        sku=p_data["sku"],
        defaults={
            "category": categories["Installationsmaterial"],
            "name": p_data["name"],
            "unit": "set",
            "purchase_price_net": Decimal(str(p_data["purchase"])),
            "sales_price_net": Decimal(str(p_data["sales"])),
            "vat_rate": Decimal(str(p_data["vat"])),
            "stock_quantity": 20,
            "min_stock_level": 5,
        }
    )
    status = "[+]" if created else "[o]"
    print(f"  {status} {product.sku} - {product.name}")

# Dienstleistungen
service_products = [
    {"sku": "SVC-INSTALL-BASE", "name": "Installation Basis (< 5 kWp)", "purchase": 300, "sales": 600, "vat": 0.19},
    {"sku": "SVC-INSTALL-MID", "name": "Installation Mittel (5-10 kWp)", "purchase": 500, "sales": 950, "vat": 0.19},
    {"sku": "SVC-INSTALL-LARGE", "name": "Installation Groß (> 10 kWp)", "purchase": 800, "sales": 1500, "vat": 0.19},
    {"sku": "SVC-PLANNING", "name": "Planung und Dokumentation", "purchase": 100, "sales": 250, "vat": 0.19},
    {"sku": "SVC-ELECTRICIAN", "name": "Elektrikerarbeit pro Stunde", "purchase": 45, "sales": 85, "vat": 0.19},
]

for p_data in service_products:
    product, created = Product.objects.get_or_create(
        sku=p_data["sku"],
        defaults={
            "category": categories["Dienstleistungen"],
            "name": p_data["name"],
            "unit": "hour" if "Stunde" in p_data["name"] else "lump_sum",
            "purchase_price_net": Decimal(str(p_data["purchase"])),
            "sales_price_net": Decimal(str(p_data["sales"])),
            "vat_rate": Decimal(str(p_data["vat"])),
        }
    )
    status = "[+]" if created else "[o]"
    print(f"  {status} {product.sku} - {product.name}")

# Zubehör
accessory_products = [
    {"sku": "ACC-WALLBOX-11KW", "name": "Wallbox 11kW", "purchase": 600, "sales": 1100, "vat": 0.19},
    {"sku": "ACC-WALLBOX-22KW", "name": "Wallbox 22kW", "purchase": 800, "sales": 1400, "vat": 0.19},
    {"sku": "ACC-MONITOR", "name": "Energie-Monitoring-System", "purchase": 200, "sales": 380, "vat": 0.19},
    {"sku": "ACC-OPTIMIZER", "name": "Leistungsoptimierer", "purchase": 50, "sales": 95, "vat": 0.19},
]

for p_data in accessory_products:
    product, created = Product.objects.get_or_create(
        sku=p_data["sku"],
        defaults={
            "category": categories["Zubehör"],
            "name": p_data["name"],
            "unit": "piece",
            "purchase_price_net": Decimal(str(p_data["purchase"])),
            "sales_price_net": Decimal(str(p_data["sales"])),
            "vat_rate": Decimal(str(p_data["vat"])),
            "stock_quantity": 10,
            "min_stock_level": 3,
        }
    )
    status = "[+]" if created else "[o]"
    print(f"  {status} {product.sku} - {product.name}")

print("\n" + "="*60)
print("Zusammenfassung:")
print("="*60)
print(f"Kategorien: {ProductCategory.objects.count()}")
print(f"Produkte: {Product.objects.count()}")
print("\nProdukte pro Kategorie:")
for cat in ProductCategory.objects.all():
    count = cat.products.count()
    print(f"  - {cat.name}: {count} Produkte")

print("\n[SUCCESS] Test-Daten erfolgreich erstellt!")
