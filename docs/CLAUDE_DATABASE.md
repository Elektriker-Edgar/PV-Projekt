# CLAUDE_DATABASE.md - Datenbank & Migrationen

> Detaillierte Dokumentation der Datenbank-Modelle, Migrationen und Schema

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)

---

## 📊 Datenbank-Schema Übersicht

**Database Engine:** PostgreSQL (Production) / SQLite (Development)

### Hauptmodelle

| App | Model | Beschreibung | Wichtigste Felder |
|-----|-------|--------------|-------------------|
| `core` | User | Erweiterte User-Klasse | email, role, is_installer |
| `core` | Customer | Kundenstammdaten | name, email, phone, type |
| `core` | Site | Installationsorte | address, customer, grid_operator |
| `quotes` | **PriceConfig** | Preiskonfiguration | price_type, value, is_percentage |
| `quotes` | Quote | Angebote | customer, site, total_price, status |
| `quotes` | Precheck | Vorprüfungen | customer, site, price_data |
| `quotes` | Component | Komponenten-Katalog | type, manufacturer, model, price |
| `inventory` | InventoryItem | Lagerbestand | component, quantity, location |
| `orders` | Order | Aufträge | quote, status, scheduled_date |
| `grid` | GridOperator | Netzbetreiber | name, region, registration_url |

---

## 🔑 PriceConfig Model (Detailliert)

**Datei:** `apps/quotes/models.py`
**Beschreibung:** Zentrale Preiskonfiguration für alle Berechnungen

### Model-Definition

```python
class PriceConfig(models.Model):
    """
    Konfiguration für dynamische Preisberechnungen.
    Alle Preise werden in der Datenbank gespeichert und können
    über Django Admin angepasst werden.
    """

    PRICE_TYPES = [
        # Anfahrtskosten (ortbasiert)
        ('travel_zone_0', 'Anfahrt Zone 0 (Hamburg)'),
        ('travel_zone_30', 'Anfahrt Zone 30 (bis 30km)'),
        ('travel_zone_60', 'Anfahrt Zone 60 (bis 60km)'),

        # Zuschläge
        ('surcharge_tt_grid', 'TT-Netz Zuschlag'),
        ('surcharge_selective_fuse', 'Selektive Vorsicherung'),
        ('surcharge_cable_meter', 'Kabel pro Meter (über 15m)'),  # Legacy

        # Rabatte
        ('discount_complete_kit', 'Komplett-Kit Rabatt %'),

        # Pakete (Basis-Installation)
        ('package_basis', 'Basis-Paket'),
        ('package_plus', 'Plus-Paket'),
        ('package_pro', 'Pro-Paket'),

        # Material
        ('material_ac_wiring', 'AC-Verkabelung'),
        ('material_spd', 'Überspannungsschutz'),
        ('material_meter_upgrade', 'Zählerplatz-Ertüchtigung'),
        ('material_storage_kwh', 'Speicher pro kWh'),

        # Wallbox-Preise (NEU in v1.1.0)
        ('wallbox_base_4kw', 'Wallbox Installation <4kW'),
        ('wallbox_base_11kw', 'Wallbox Installation 11kW'),
        ('wallbox_base_22kw', 'Wallbox Installation 22kW'),
        ('wallbox_stand_mount', 'Wallbox Ständer-Montage Zuschlag'),
        ('wallbox_pv_surplus', 'PV-Überschussladen'),

        # Variable Kabelpreise Wechselrichter (NEU in v1.1.0)
        ('cable_wr_up_to_5kw', 'WR-Kabel bis 5kW pro Meter'),
        ('cable_wr_5_to_10kw', 'WR-Kabel 5-10kW pro Meter'),
        ('cable_wr_above_10kw', 'WR-Kabel über 10kW pro Meter'),

        # Variable Kabelpreise Wallbox (NEU in v1.1.0)
        ('cable_wb_4kw', 'Wallbox-Kabel <4kW pro Meter'),
        ('cable_wb_11kw', 'Wallbox-Kabel 11kW pro Meter'),
        ('cable_wb_22kw', 'Wallbox-Kabel 22kW pro Meter'),
    ]

    price_type = models.CharField(
        max_length=50,
        choices=PRICE_TYPES,
        unique=True,
        help_text="Eindeutiger Bezeichner für den Preistyp"
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Preis in Euro oder Prozentsatz (je nach is_percentage)"
    )
    is_percentage = models.BooleanField(
        default=False,
        help_text="Ist der Wert ein Prozentsatz? (z.B. für Rabatte)"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optionale Beschreibung des Preises"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Preiskonfiguration"
        verbose_name_plural = "Preiskonfigurationen"
        ordering = ['price_type']

    def __str__(self):
        if self.is_percentage:
            return f"{self.get_price_type_display()}: {self.value}%"
        return f"{self.get_price_type_display()}: {self.value}€"
```

### Standard-Preise (Seeded in Migrationen)

| price_type | value | is_percentage | Beschreibung |
|------------|-------|---------------|--------------|
| `travel_zone_0` | 0.00€ | ❌ | Hamburg |
| `travel_zone_30` | 50.00€ | ❌ | bis 30km |
| `travel_zone_60` | 95.00€ | ❌ | bis 60km |
| `surcharge_tt_grid` | 150.00€ | ❌ | TT-Netz |
| `surcharge_selective_fuse` | 220.00€ | ❌ | Sicherung >35A |
| `discount_complete_kit` | 15.00 | ✅ | 15% Rabatt |
| `package_basis` | 890.00€ | ❌ | Basis-Paket |
| `package_plus` | 1490.00€ | ❌ | Plus-Paket |
| `package_pro` | 2290.00€ | ❌ | Pro-Paket |
| `material_ac_wiring` | 180.00€ | ❌ | AC-Verkabelung |
| `material_spd` | 320.00€ | ❌ | Überspannungsschutz |
| `material_meter_upgrade` | 450.00€ | ❌ | Zählerplatz |
| `material_storage_kwh` | 800.00€ | ❌ | Pro kWh |
| `wallbox_base_4kw` | 890.00€ | ❌ | <4kW Wallbox |
| `wallbox_base_11kw` | 1290.00€ | ❌ | 11kW Wallbox |
| `wallbox_base_22kw` | 1690.00€ | ❌ | 22kW Wallbox |
| `wallbox_stand_mount` | 350.00€ | ❌ | Ständer-Montage |
| `wallbox_pv_surplus` | 0.00€ | ❌ | PV-Überschuss |
| `cable_wr_up_to_5kw` | 15.00€ | ❌ | WR-Kabel ≤5kW/m |
| `cable_wr_5_to_10kw` | 25.00€ | ❌ | WR-Kabel 5-10kW/m |
| `cable_wr_above_10kw` | 35.00€ | ❌ | WR-Kabel >10kW/m |
| `cable_wb_4kw` | 12.00€ | ❌ | Wallbox-Kabel 4kW/m |
| `cable_wb_11kw` | 20.00€ | ❌ | Wallbox-Kabel 11kW/m |
| `cable_wb_22kw` | 30.00€ | ❌ | Wallbox-Kabel 22kW/m |

---

## 📝 Migrationen (Chronologisch)

### Migration 0001 - Initial

**Datei:** `apps/quotes/migrations/0001_initial.py`
**Status:** ✅ Applied

Erstellt initiale Modelle:
- PriceConfig
- Quote
- Precheck
- Component

### Migration 0002 - Seed Components

**Datei:** `apps/quotes/migrations/0002_seed_components.py`
**Status:** ✅ Applied

Seeded initiale Komponenten-Daten (Wechselrichter, Speicher).

### Migration 0003 - Seed Price Config

**Datei:** `apps/quotes/migrations/0003_seed_price_config_and_components.py`
**Status:** ✅ Applied

Seeded initiale PriceConfig-Einträge (14 Basis-Preise).

### Migration 0005 - Alter PriceConfig PRICE_TYPES

**Datei:** `apps/quotes/migrations/0005_alter_priceconfig_price_type.py`
**Status:** ✅ Applied
**Erstellt:** 2025-01-08

**Zweck:** Erweitert PRICE_TYPES um Wallbox- und variable Kabel-Optionen

**Änderungen:**
```python
# VORHER (14 Types):
PRICE_TYPES = [
    ('travel_zone_0', ...),
    ('travel_zone_30', ...),
    # ... 14 total
]

# NACHHER (25 Types):
PRICE_TYPES = [
    # Alte Types (14)
    ('travel_zone_0', ...),
    # ...

    # NEU: Wallbox (5)
    ('wallbox_base_4kw', ...),
    ('wallbox_base_11kw', ...),
    ('wallbox_base_22kw', ...),
    ('wallbox_stand_mount', ...),
    ('wallbox_pv_surplus', ...),

    # NEU: Variable WR-Kabelpreise (3)
    ('cable_wr_up_to_5kw', ...),
    ('cable_wr_5_to_10kw', ...),
    ('cable_wr_above_10kw', ...),

    # NEU: Variable Wallbox-Kabelpreise (3)
    ('cable_wb_4kw', ...),
    ('cable_wb_11kw', ...),
    ('cable_wb_22kw', ...),
]
```

**Dependencies:**
```python
dependencies = [
    ('quotes', '0003_seed_price_config_and_components'),
]
```

**Migration-Code:**
```python
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0003_seed_price_config_and_components'),
    ]

    operations = [
        migrations.AlterField(
            model_name='priceconfig',
            name='price_type',
            field=models.CharField(
                choices=[
                    # ... alle 25 PRICE_TYPES
                ],
                max_length=50,
                unique=True
            ),
        ),
    ]
```

### Migration 0006 - Seed Wallbox Pricing

**Datei:** `apps/quotes/migrations/0006_seed_wallbox_pricing.py`
**Status:** ✅ Applied
**Erstellt:** 2025-01-08

**Zweck:** Fügt 11 neue PriceConfig-Einträge für Wallbox-Preise hinzu

**Seeded Daten:**

```python
from decimal import Decimal

def seed_wallbox_pricing(apps, schema_editor):
    PriceConfig = apps.get_model('quotes', 'PriceConfig')

    # Wallbox Base-Preise
    wallbox_prices = [
        ('wallbox_base_4kw', Decimal('890.00'), False, 'Wallbox Installation <4kW'),
        ('wallbox_base_11kw', Decimal('1290.00'), False, 'Wallbox Installation 11kW'),
        ('wallbox_base_22kw', Decimal('1690.00'), False, 'Wallbox Installation 22kW'),
        ('wallbox_stand_mount', Decimal('350.00'), False, 'Wallbox Ständer-Montage Zuschlag'),
        ('wallbox_pv_surplus', Decimal('0.00'), False, 'PV-Überschussladen (aktuell kostenlos)'),
    ]

    # Variable WR-Kabelpreise
    wr_cable_prices = [
        ('cable_wr_up_to_5kw', Decimal('15.00'), False, 'WR-Kabel bis 5kW pro Meter'),
        ('cable_wr_5_to_10kw', Decimal('25.00'), False, 'WR-Kabel 5-10kW pro Meter'),
        ('cable_wr_above_10kw', Decimal('35.00'), False, 'WR-Kabel über 10kW pro Meter'),
    ]

    # Variable Wallbox-Kabelpreise
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
                'description': description
            }
        )
```

**Reverse-Funktion:**
```python
def reverse_seed_wallbox_pricing(apps, schema_editor):
    PriceConfig = apps.get_model('quotes', 'PriceConfig')

    # Alle 11 Wallbox-Einträge löschen
    wallbox_types = [
        'wallbox_base_4kw', 'wallbox_base_11kw', 'wallbox_base_22kw',
        'wallbox_stand_mount', 'wallbox_pv_surplus',
        'cable_wr_up_to_5kw', 'cable_wr_5_to_10kw', 'cable_wr_above_10kw',
        'cable_wb_4kw', 'cable_wb_11kw', 'cable_wb_22kw'
    ]

    PriceConfig.objects.filter(price_type__in=wallbox_types).delete()
```

**Dependencies:**
```python
dependencies = [
    ('quotes', '0005_alter_priceconfig_price_type'),
]
```

**Ausführen:**
```bash
python manage.py migrate
```

**Rückgängig machen:**
```bash
python manage.py migrate quotes 0005
```

---

## 🔄 Migration-Historie & Known Issues

### Issue: Migration 0004 fehlte

**Problem:**
- Migration 0005 hatte ursprünglich Dependency auf `0004_add_wallbox_pricing`
- Migration 0004 existierte nicht im Code (wurde gelöscht)
- `python manage.py migrate` schlug fehl

**Lösung:**
1. Migration 0005 Dependencies auf `0003` geändert
2. Neue Migration 0006 für Wallbox-Seeding erstellt
3. Erfolgreich migriert

**Lessons Learned:**
- Niemals Migrationen aus Code löschen, wenn sie in DB angewendet wurden
- Bei Konflikten: Neue Migration erstellen statt alte zu ändern
- Immer Reverse-Funktionen implementieren

---

## 🗄️ Weitere Modelle (Kurzübersicht)

### Quote Model

**Datei:** `apps/quotes/models.py`

```python
class Quote(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('sent', 'Versendet'),
        ('approved', 'Genehmigt'),
        ('rejected', 'Abgelehnt'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Precheck Model

**Datei:** `apps/quotes/models.py`

```python
class Precheck(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True)

    # Formular-Daten (JSON)
    form_data = models.JSONField(default=dict)
    price_data = models.JSONField(default=dict)

    # Status
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
```

### Component Model

**Datei:** `apps/quotes/models.py`

```python
class Component(models.Model):
    TYPE_CHOICES = [
        ('inverter', 'Wechselrichter'),
        ('storage', 'Speicher'),
        ('wallbox', 'Wallbox'),
        ('other', 'Sonstiges'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
```

---

## 🔧 Häufige Datenbank-Operationen

### Preise aktualisieren

```python
# Django Shell
python manage.py shell

from apps.quotes.models import PriceConfig
from decimal import Decimal

# Einzelnen Preis ändern
config = PriceConfig.objects.get(price_type='wallbox_base_11kw')
config.value = Decimal('1390.00')
config.save()

# Alle Wallbox-Preise anzeigen
wallbox_prices = PriceConfig.objects.filter(price_type__startswith='wallbox')
for p in wallbox_prices:
    print(f"{p.price_type}: {p.value}€")

# Kabelpreise anzeigen
cable_prices = PriceConfig.objects.filter(price_type__startswith='cable')
for p in cable_prices:
    print(f"{p.price_type}: {p.value}€/m")
```

### Neue PriceConfig-Einträge hinzufügen

```python
from apps.quotes.models import PriceConfig
from decimal import Decimal

# Neuen Preis hinzufügen (manuell)
PriceConfig.objects.create(
    price_type='custom_price',
    value=Decimal('150.00'),
    is_percentage=False,
    description='Mein Custom-Preis'
)
```

**ACHTUNG:** Beim Hinzufügen neuer `price_type` Werte:
1. Erst Migration 000X_alter_priceconfig_price_type.py erstellen
2. PRICE_TYPES in models.py erweitern
3. Migration ausführen
4. Daten seeden

---

## 📊 Datenbank-Backup & Restore

### SQLite (Development)

```bash
# Backup
cp db.sqlite3 db.sqlite3.backup

# Restore
cp db.sqlite3.backup db.sqlite3
```

### PostgreSQL (Production)

```bash
# Backup
pg_dump -U postgres -d pv_service_prod > backup.sql

# Restore
psql -U postgres -d pv_service_prod < backup.sql
```

---

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)
**Siehe auch:**
- [CLAUDE_API.md](CLAUDE_API.md) - API & Backend
- [CLAUDE_DEPLOYMENT.md](CLAUDE_DEPLOYMENT.md) - Deployment & Testing
