# CLAUDE_DATABASE.md - Datenbank & Migrationen

> Detaillierte Dokumentation der Datenbank-Modelle, Migrationen und Schema

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)

---

## 📊 Datenbank-Schema Übersicht

**Database Engine:** PostgreSQL (Production) / SQLite (Development)

### Hauptmodelle

| App | Model | Beschreibung | Wichtigste Felder |
|-----|-------|--------------|-------------------|
| `core` | User | Erweiterte User-Klasse | username/email, role, phone |
| `core` | Customer | Kundenstammdaten | name, email, phone, type |
| `core` | Site | Installationsorte | customer, address, building_type, main_fuse_ampere |
| `quotes` | **PriceConfig** | Preiskonfiguration | price_type, value, is_percentage |
| `quotes` | **ProductCategory** | Produktkategorien | name, description, sort_order |
| `quotes` | **Product** | Produktkatalog | sku, name, category, purchase_price, sales_price |
| `quotes` | Quote | Angebote | precheck, quote_number, subtotal/total, status |
| `quotes` | Precheck | Vorprüfungen | site, Leistungs- & Installationsdaten |
| `quotes` | Component | Komponenten-Katalog | name, type, vendor, sku, unit_price |
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

### Migration 0020 - Add Location Choices to Precheck

**Datei:** `apps/quotes/migrations/0020_add_location_choices.py`
**Status:** ✅ Applied
**Erstellt:** 2025-01-16

**Zweck:** Fügt CHOICES zu inverter_location und storage_location Feldern hinzu

**Änderungen:**
- `Precheck.inverter_location`: CharField → CharField mit INVERTER_LOCATION_CHOICES
- `Precheck.storage_location`: CharField → CharField mit STORAGE_LOCATION_CHOICES

**Betroffene Felder:**
```python
INVERTER_LOCATION_CHOICES = [
    ('basement', 'Keller'),
    ('garage', 'Garage'),
    ('attic', 'Dachboden'),
    ('utility_room', 'Hauswirtschaftsraum'),
    ('outdoor', 'Außenbereich (wettergeschützt)'),
    ('other', 'Anderer Ort'),
]

STORAGE_LOCATION_CHOICES = [
    ('basement', 'Keller'),
    ('garage', 'Garage'),
    ('attic', 'Dachboden'),
    ('utility_room', 'Hauswirtschaftsraum'),
    ('outdoor', 'Außenbereich (wettergeschützt)'),
    ('other', 'Anderer Ort'),
]
```

### Migration 0021 - Add same_as_inverter to Storage Location

**Datei:** `apps/quotes/migrations/0021_alter_precheck_storage_location.py`
**Status:** ✅ Applied
**Erstellt:** 2025-01-16

**Zweck:** Fügt 'same_as_inverter' Option zu STORAGE_LOCATION_CHOICES hinzu

**Grund:** Template verwendet diesen Wert, führte zu Validierungsfehlern

**Aktualisierte STORAGE_LOCATION_CHOICES:**
```python
STORAGE_LOCATION_CHOICES = [
    ('same_as_inverter', 'Gleicher Ort wie Wechselrichter'),  # NEU
    ('basement', 'Keller'),
    ('garage', 'Garage'),
    ('attic', 'Dachboden'),
    ('utility_room', 'Hauswirtschaftsraum'),
    ('outdoor', 'Außenbereich (wettergeschützt)'),
    ('other', 'Anderer Ort'),
]
```

### Migration 0022 - Add Notes to Quote

**Datei:** `apps/quotes/migrations/0022_add_quote_notes.py`
**Status:** ✅ Applied
**Erstellt:** 2025-01-16

**Zweck:** Fügt notes TextField zu Quote Model hinzu

**Neues Feld:**
```python
notes = models.TextField(
    blank=True,
    help_text='Interne Notizen zu Sonderwünschen oder Anpassungen'
)
```

**Use Case:** Erfassung von:
- Kundenwünschen aus Precheck-Notizen
- Gründen für manuelle Anpassungen
- Hinweisen für andere Mitarbeiter

### Migration 0023 - Add VAT Rate to QuoteItem

**Datei:** `apps/quotes/migrations/0023_add_quoteitem_vat_rate.py`
**Status:** ✅ Applied
**Erstellt:** 2025-01-16

**Zweck:** Fügt vat_rate Feld zu QuoteItem hinzu für individuelle MwSt.-Sätze

**Neues Feld:**
```python
vat_rate = models.DecimalField(
    max_digits=5,
    decimal_places=2,
    default=Decimal('19.00'),
    help_text='MwSt.-Satz in Prozent'
)
```

**Use Cases:**
- Standardsatz: 19% (Elektroinstallation)
- Ermäßigter Satz: 7% (bestimmte Lieferungen)
- Nullsteuersatz: 0% (PV-Anlagen unter bestimmten Bedingungen)
- Split-MwSt.-Berechnung bei gemischten Positionen

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
        ('review', 'In Prüfung'),
        ('approved', 'Freigegeben'),
        ('sent', 'Versendet'),
        ('accepted', 'Angenommen'),
        ('rejected', 'Abgelehnt'),
        ('expired', 'Abgelaufen'),
    ]

    precheck = models.OneToOneField(Precheck, on_delete=models.CASCADE)
    quote_number = models.CharField(max_length=20, unique=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'))
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    pdf_url = models.URLField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quotes')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_quotes')
    approved_at = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
```

### Precheck Model

**Datei:** `apps/quotes/models.py`

```python
class Precheck(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    # Gebäude & Bauzustand
    building_type = models.CharField(max_length=20, choices=BuildingType.choices, blank=True, default='')
    construction_year = models.IntegerField(null=True, blank=True)
    has_renovation = models.BooleanField(default=False)
    renovation_year = models.IntegerField(null=True, blank=True)

    # Elektrik / Schutzmaßnahmen
    has_sls_switch = models.BooleanField(default=False)
    sls_switch_details = models.TextField(blank=True, default='')
    has_surge_protection_ac = models.BooleanField(default=False)
    surge_protection_ac_details = models.TextField(blank=True, default='')
    has_surge_protection_dc = models.BooleanField(default=False)
    has_grounding = models.CharField(max_length=10, choices=GroundingChoice.choices, blank=True, default='')
    has_deep_earth = models.CharField(max_length=10, choices=GroundingChoice.choices, blank=True, default='')
    grounding_details = models.TextField(blank=True, default='')

    # Montageorte & Netz
    inverter_location = models.CharField(max_length=50, choices=InverterLocation.choices, blank=True, default='')
    storage_location = models.CharField(max_length=50, choices=StorageLocation.choices, blank=True, default='')
    distance_meter_to_inverter = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    grid_operator = models.CharField(max_length=100, blank=True, default='')

    # Anlagenleistung & Komponenten
    desired_power_kw = models.DecimalField(max_digits=5, decimal_places=2)
    storage_kwh = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feed_in_mode = models.CharField(max_length=20, choices=FeedInMode.choices, blank=True, default='')
    requires_backup_power = models.BooleanField(default=False)
    backup_power_details = models.TextField(blank=True, default='')
    own_components = models.BooleanField(default=False)
    own_material_description = models.TextField(blank=True, default='')

    # Zusatzgeräte / Wallbox
    has_heat_pump = models.BooleanField(default=False)
    heat_pump_cascade = models.BooleanField(default=False)
    heat_pump_details = models.TextField(blank=True, default='')
    wallbox = models.BooleanField(default=False)
    wallbox_class = models.CharField(max_length=4, choices=WallboxClass.choices, blank=True, default='')
    wallbox_mount = models.CharField(max_length=10, choices=WallboxMount.choices, blank=True, default='')
    wallbox_cable_prepared = models.BooleanField(default=False)
    wallbox_cable_length_m = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    PACKAGE_CHOICES = [
        ('', 'Kein Paket ausgewählt'),
        ('basis', 'Basis-Paket'),
        ('plus', 'Plus-Paket'),
        ('pro', 'Pro-Paket'),
    ]
    package_choice = models.CharField(max_length=10, choices=PACKAGE_CHOICES, blank=True, default='')
    is_express_package = models.BooleanField(default=False)
    wallbox_pv_surplus = models.BooleanField(default=False)

    # Uploads & sonstige Angaben
    meter_cabinet_photo = models.FileField(upload_to='precheck/meter_cabinet/%Y/%m/', null=True, blank=True,
                                           validators=[validate_media_file])
    hak_photo = models.FileField(upload_to='precheck/hak/%Y/%m/', null=True, blank=True,
                                 validators=[validate_media_file])
    location_photo = models.FileField(upload_to='precheck/locations/%Y/%m/', null=True, blank=True,
                                      validators=[validate_media_file])
    cable_route_photo = models.FileField(upload_to='precheck/cables/%Y/%m/', null=True, blank=True,
                                         validators=[validate_media_file])
    component_files = models.TextField(default='[]', help_text="Legacy JSON mit Datenblättern")
    preferred_timeframes = models.TextField(default='[]', help_text="JSON Liste gewünschter Zeitfenster")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # (siehe models.py für alle weiteren Properties wie helper-Methoden & PrecheckPhoto)
```

### Component Model

**Datei:** `apps/quotes/models.py`

```python
class Component(models.Model):
    COMPONENT_TYPES = [
        ('inverter', 'Wechselrichter'),
        ('battery', 'Speicher'),
        ('spd', 'Überspannungsschutz'),
        ('meter', 'Zählerplatz'),
        ('cable', 'Kabel'),
        ('switch', 'Schalter'),
        ('other', 'Sonstiges'),
    ]

    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    vendor = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, unique=True)
    datasheet_url = models.URLField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    compatible_with = models.ManyToManyField('self', blank=True, symmetrical=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 📦 Produktkatalog-Modelle (NEU v1.2.0)

### ProductCategory Model

**Datei:** `apps/quotes/models.py` (Zeilen 273-297)
**Erstellt:** 2025-11-11

```python
class ProductCategory(models.Model):
    """Produktkategorien für den Artikelkatalog"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Kategoriename")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    sort_order = models.IntegerField(default=0, verbose_name="Sortierreihenfolge")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "Produktkategorie"
        verbose_name_plural = "Produktkategorien"

    def get_product_count(self):
        """Anzahl aktiver Produkte in dieser Kategorie"""
        return self.products.filter(is_active=True).count()
```

### Product Model

**Datei:** `apps/quotes/models.py` (Zeilen 299-419)
**Erstellt:** 2025-11-11

```python
class Product(models.Model):
    """Artikelkatalog für Produkte und Dienstleistungen"""

    UNIT_CHOICES = [
        ('piece', 'Stück'), ('meter', 'Meter'), ('hour', 'Stunde'),
        ('kwh', 'kWh'), ('kwp', 'kWp'), ('set', 'Set'),
        ('package', 'Paket'), ('lump_sum', 'Pauschal'),
    ]

    VAT_RATE_CHOICES = [
        (Decimal('0.00'), '0% (Steuerfrei)'),
        (Decimal('0.07'), '7% (Ermäßigt)'),
        (Decimal('0.19'), '19% (Standard)'),
    ]

    # Basis-Felder
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT,
                                 related_name='products')
    name = models.CharField(max_length=200, verbose_name="Bezeichnung")
    sku = models.CharField(max_length=100, unique=True, verbose_name="Artikelnummer (SKU)")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')

    # Preise (Netto)
    purchase_price_net = models.DecimalField(max_digits=10, decimal_places=2,
                                             default=Decimal('0.00'))
    sales_price_net = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2,
                                   choices=VAT_RATE_CHOICES, default=Decimal('0.19'))

    # Lagerbestand (optional)
    stock_quantity = models.IntegerField(default=0, blank=True, null=True)
    min_stock_level = models.IntegerField(default=0, blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Zusatzinformationen
    manufacturer = models.CharField(max_length=200, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    # Berechnete Properties
    @property
    def sales_price_gross(self):
        """Verkaufspreis brutto (berechnet)"""
        return self.sales_price_net * (1 + self.vat_rate)

    @property
    def purchase_price_gross(self):
        """Einkaufspreis brutto (berechnet)"""
        return self.purchase_price_net * (1 + self.vat_rate)

    @property
    def margin_amount(self):
        """Marge in Euro"""
        return self.sales_price_net - self.purchase_price_net

    @property
    def margin_percentage(self):
        """Marge in Prozent"""
        if self.purchase_price_net > 0:
            return ((self.sales_price_net - self.purchase_price_net) /
                    self.purchase_price_net) * 100
        return Decimal('0.00')

    class Meta:
        ordering = ['name']
        verbose_name = "Produkt"
        verbose_name_plural = "Produkte"
```

### Migration 0010 - ProductCategory & Product

**Datei:** `apps/quotes/migrations/0010_productcategory_product.py`
**Status:** ✅ Applied
**Erstellt:** 2025-11-11

```python
class Migration(migrations.Migration):
    dependencies = [
        ('quotes', '0006_seed_wallbox_pricing'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.TextField(blank=True)),
                ('sort_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('sku', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('unit', models.CharField(max_length=20, choices=UNIT_CHOICES)),
                ('purchase_price_net', models.DecimalField(max_digits=10, decimal_places=2)),
                ('sales_price_net', models.DecimalField(max_digits=10, decimal_places=2)),
                ('vat_rate', models.DecimalField(max_digits=4, decimal_places=2)),
                ('stock_quantity', models.IntegerField(blank=True, null=True)),
                ('min_stock_level', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('manufacturer', models.CharField(max_length=200, blank=True)),
                ('supplier', models.CharField(max_length=200, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=models.PROTECT, to='quotes.productcategory')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
```

### Test-Daten

**Script:** `create_test_products.py`
**Erstellt:** 2025-11-11

**Erstellte Kategorien (7):**
1. **Precheck-Artikel** - Artikel für Precheck-Kalkulation (6 Produkte)
2. **Wechselrichter** - Wechselrichter für PV-Anlagen (4 Produkte)
3. **Speicher** - Batteriespeicher-Systeme (3 Produkte)
4. **Installationsmaterial** - Material für die Installation (4 Produkte)
5. **Kabel** - DC- und AC-Kabel (4 Produkte)
6. **Dienstleistungen** - Montage, Planung und Beratung (5 Produkte)
7. **Zubehör** - Diverses Zubehör (4 Produkte)

**Beispiel-Produkte:**
```python
# Precheck-Artikel
PRECHK-BASE      | Basis-Paket                    | 150€ → 299€  (99,3% Marge)
PRECHK-PLUS      | Plus-Paket                     | 250€ → 499€  (99,6% Marge)
PRECHK-PRO       | Pro-Paket                      | 400€ → 799€  (99,8% Marge)
TRAVEL-0         | Anfahrt Zone 0 (Hamburg)       | 20€  → 50€   (150% Marge)
TRAVEL-30        | Anfahrt Zone 30 (bis 30km)     | 30€  → 75€   (150% Marge)
TRAVEL-60        | Anfahrt Zone 60 (bis 60km)     | 50€  → 125€  (150% Marge)

# Wechselrichter
INV-FRONIUS-5    | Fronius Symo 5.0-3-M           | 800€ → 1200€ (50% Marge)
INV-FRONIUS-10   | Fronius Symo 10.0-3-M          | 1200€ → 1800€ (50% Marge)
INV-KOSTAL-8     | KOSTAL PLENTICORE plus 8.5     | 900€ → 1400€ (55,6% Marge)
INV-SMA-6        | SMA Sunny Tripower 6.0         | 850€ → 1300€ (52,9% Marge)

# Wallboxen
ACC-WALLBOX-11KW | Wallbox 11kW                   | 600€ → 1100€ (83,3% Marge)
ACC-WALLBOX-22KW | Wallbox 22kW                   | 800€ → 1400€ (75% Marge)
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
