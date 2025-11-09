# CLAUDE_API.md - API & Backend Dokumentation

> Detaillierte Dokumentation aller API-Endpoints, Backend-Logik und Preisberechnung

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)

---

## 📊 PriceConfig Model (Database-Driven Pricing)

**Datei:** `apps/quotes/models.py`

### Model-Definition

```python
class PriceConfig(models.Model):
    """Konfiguration für Preisberechnungen"""

    PRICE_TYPES = [
        # Anfahrtskosten
        ('travel_zone_0', 'Anfahrt Zone 0 (Hamburg)'),
        ('travel_zone_30', 'Anfahrt Zone 30 (bis 30km)'),
        ('travel_zone_60', 'Anfahrt Zone 60 (bis 60km)'),

        # Zuschläge
        ('surcharge_tt_grid', 'TT-Netz Zuschlag'),
        ('surcharge_selective_fuse', 'Selektive Vorsicherung'),
        ('surcharge_cable_meter', 'Kabel pro Meter (über 15m)'),

        # Rabatte
        ('discount_complete_kit', 'Komplett-Kit Rabatt %'),

        # Pakete
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

    price_type = models.CharField(max_length=50, choices=PRICE_TYPES, unique=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    is_percentage = models.BooleanField(default=False, help_text="Ist der Wert ein Prozentsatz?")
    description = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
```

### Verwendung im Code

```python
# Helper-Funktion zum Abrufen von Preisen
def _pc(key: str, default: Decimal) -> Decimal:
    """
    Holt einen Preis aus der Datenbank.
    Falls nicht vorhanden, wird der default-Wert zurückgegeben.
    """
    try:
        obj = PriceConfig.objects.get(price_type=key)
        return obj.value
    except PriceConfig.DoesNotExist:
        return default

# Beispiele:
wallbox_price = _pc('wallbox_base_11kw', Decimal('1290.00'))
cable_price = _pc('cable_wr_5_to_10kw', Decimal('25.00'))
travel_cost = _pc('travel_zone_0', Decimal('0.00'))
```

---

## 🔌 API-Endpoints Übersicht

| Endpoint | Method | Zweck | Auth | CSRF |
|----------|--------|-------|------|------|
| `/api/pricing/preview/` | POST | Live-Preisberechnung | ❌ AllowAny | Exempt |
| `/api/precheck/` | POST | Precheck erstellen | ❌ AllowAny | Required |
| `/api/components/` | GET | Komponenten-Liste | ❌ AllowAny | N/A |
| `/api/quotes/<pk>/approve/` | POST | Angebot freigeben | ✅ Admin | Required |

---

## 💰 Pricing API - Live-Preisberechnung

**Datei:** `apps/quotes/api_views.py`

### Endpoint Details

**URL:** `POST /api/pricing/preview/`
**Permissions:** `AllowAny` (öffentlich zugänglich)
**CSRF:** Exempt (kann ohne CSRF-Token aufgerufen werden)

### Request Parameter

```python
{
    # Standort & Elektro
    "site_address": str,                    # Für Anfahrtskosten-Berechnung
    "main_fuse_ampere": int,                # Für Zuschlag selektive Sicherung
    "grid_type": str,                       # '3p', '1p', 'TT'
    "distance_meter_to_inverter": Decimal,  # Entfernung Zähler→WR in Metern

    # PV-System
    "desired_power_kw": Decimal,            # WR-Leistung (für Kabelpreis)
    "inverter_class": str,                  # '1kva', '3kva', '5kva', '10kva'
    "storage_kwh": Decimal,                 # Speichergröße (0 = kein Speicher)
    "own_components": bool,                 # Kunde bringt eigene Komponenten

    # Wallbox-Parameter (NEU)
    "has_wallbox": bool,                    # Wallbox gewünscht?
    "wallbox_power": str,                   # '4kw', '11kw', '22kw'
    "wallbox_mount": str,                   # 'wall', 'stand'
    "wallbox_cable_installed": bool,        # Kabel bereits verlegt?
    "wallbox_cable_length": Decimal,        # Kabellänge in Metern
    "wallbox_pv_surplus": bool,             # PV-Überschussladen gewünscht?
}
```

### Response Format

```json
{
    "package": "pro",              // 'basis', 'plus', 'pro'
    "basePrice": 2290.0,           // Paket-Grundpreis
    "travelCost": 0.0,             // Anfahrtskosten
    "surcharges": 125.0,           // Zuschläge (inkl. WR-Kabelkosten)
    "inverterCost": 2750.0,        // WR + AC-Verkabelung + ggf. SPD/Meter
    "storageCost": 8000.0,         // Speicher-Kosten (0 wenn kein Speicher)
    "wallboxCost": 1790.0,         // Wallbox-Gesamtkosten (0 wenn keine Wallbox)
    "materialCost": 12540.0,       // Summe: inverter + storage + wallbox
    "discount": 343.5,             // Komplett-Kit Rabatt
    "total": 14611.5               // Endpreis inkl. aller Faktoren
}
```

---

## 🧮 Preisberechnung-Logik (Detailliert)

### 1. Paket-Bestimmung

```python
# Automatische Paket-Auswahl basierend auf Kundenanforderungen
if storage_kwh and storage_kwh > 0:
    package = 'pro'        # Speicher vorhanden → Pro-Paket (2.290€)
elif (desired_power and desired_power > 3) or inverter_class in ['5kva', '10kva'] or grid_type == 'TT':
    package = 'plus'       # >3kW oder TT-Netz → Plus-Paket (1.490€)
else:
    package = 'basis'      # Standard → Basis-Paket (890€)

# Basis-Preis aus DB holen
base_price = _pc({
    'basis': 'package_basis',
    'plus': 'package_plus',
    'pro': 'package_pro'
}[package], {
    'basis': Decimal('890.00'),
    'plus': Decimal('1490.00'),
    'pro': Decimal('2290.00')
}[package])
```

### 2. Anfahrtskosten (Ortbasiert)

```python
def _infer_travel_cost(address: str) -> Decimal:
    """
    Berechnet Anfahrtskosten basierend auf Adresse.

    Zonen:
    - Zone 0: Hamburg (0€)
    - Zone 30: bis 30km (50€)
    - Zone 60: bis 60km (95€)
    """
    a = (address or '').lower()

    if 'hamburg' in a:
        return _pc('travel_zone_0', Decimal('0.00'))

    if any(x in a for x in ['norderstedt', 'ahrensburg', 'pinneberg']):
        return _pc('travel_zone_30', Decimal('50.00'))

    return _pc('travel_zone_60', Decimal('95.00'))
```

### 3. Zuschläge

```python
surcharges = Decimal('0.00')

# TT-Netz Zuschlag (150€)
if grid_type == 'TT':
    surcharges += _pc('surcharge_tt_grid', Decimal('150.00'))

# Selektive Vorsicherung (220€) bei Hauptsicherung >35A
if main_fuse and main_fuse > 35:
    surcharges += _pc('surcharge_selective_fuse', Decimal('220.00'))
```

### 4. Variable WR-Kabelkosten (NEU)

```python
# Kabel über 15m → Extra-Kosten abhängig von WR-Leistung
if distance and distance > 15:
    extra_distance = distance - Decimal('15')

    # Kabelpreis abhängig von WR-Leistung
    if desired_power <= 5:
        cable_price = _pc('cable_wr_up_to_5kw', Decimal('15.00'))
    elif desired_power <= 10:
        cable_price = _pc('cable_wr_5_to_10kw', Decimal('25.00'))
    else:
        cable_price = _pc('cable_wr_above_10kw', Decimal('35.00'))

    surcharges += extra_distance * cable_price
```

**Beispiel:**
- Distanz: 20m
- WR-Leistung: 6kW
- Extra-Distanz: 20m - 15m = 5m
- Kabelpreis: 25€/m (5-10kW Klasse)
- **Kosten:** 5m × 25€/m = 125€

### 5. Wallbox-Berechnung (NEU)

```python
wallbox_cost = Decimal('0.00')

if has_wallbox:
    # 5.1 Base-Installation (abhängig von Leistungsklasse)
    if wallbox_power == '4kw':
        wallbox_cost += _pc('wallbox_base_4kw', Decimal('890.00'))
    elif wallbox_power == '11kw':
        wallbox_cost += _pc('wallbox_base_11kw', Decimal('1290.00'))
    elif wallbox_power == '22kw':
        wallbox_cost += _pc('wallbox_base_22kw', Decimal('1690.00'))

    # 5.2 Ständer-Montage Zuschlag (350€)
    if wallbox_mount == 'stand':
        wallbox_cost += _pc('wallbox_stand_mount', Decimal('350.00'))

    # 5.3 PV-Überschussladen (aktuell kostenlos)
    if wallbox_pv_surplus:
        wallbox_cost += _pc('wallbox_pv_surplus', Decimal('0.00'))

    # 5.4 Kabelverlegung (abhängig von Leistungsklasse)
    if not wallbox_cable_installed and wallbox_cable_length > 0:
        if wallbox_power == '4kw':
            cable_price = _pc('cable_wb_4kw', Decimal('12.00'))
        elif wallbox_power == '11kw':
            cable_price = _pc('cable_wb_11kw', Decimal('20.00'))
        elif wallbox_power == '22kw':
            cable_price = _pc('cable_wb_22kw', Decimal('30.00'))
        else:
            cable_price = Decimal('0.00')

        wallbox_cost += wallbox_cable_length * cable_price
```

**Beispiel:**
- Wallbox: 11kW
- Montage: Wand
- Kabel: 25m (nicht verlegt)
- PV-Überschuss: Ja
- **Berechnung:**
  - Base: 1.290€
  - Ständer: 0€
  - PV-Überschuss: 0€
  - Kabel: 25m × 20€/m = 500€
  - **Gesamt:** 1.790€

### 6. Materialkosten

```python
inverter_cost = Decimal('0.00')
storage_cost = Decimal('0.00')

if not own_components:
    # 6.1 Wechselrichter
    inv_price_map = {
        '1kva': Decimal('800.00'),
        '3kva': Decimal('1200.00'),
        '5kva': Decimal('1800.00'),
        '10kva': Decimal('2800.00')
    }
    inv_price = inv_price_map.get(inverter_class, Decimal('0.00'))

    # Optional: Preis aus Component-DB überschreiben
    try:
        db_inv = Component.objects.filter(type='inverter').first()
        if db_inv:
            inv_price = db_inv.unit_price
    except Exception:
        pass

    inverter_cost += inv_price

    # 6.2 AC-Verkabelung (immer dabei)
    inverter_cost += _pc('material_ac_wiring', Decimal('180.00'))

    # 6.3 Überspannungsschutz + Zählerplatz (nur Plus & Pro)
    if package in ['plus', 'pro']:
        inverter_cost += _pc('material_spd', Decimal('320.00'))
        inverter_cost += _pc('material_meter_upgrade', Decimal('450.00'))

    # 6.4 Speicher (nur Pro)
    if package == 'pro' and storage_kwh and storage_kwh > 0:
        storage_cost = storage_kwh * _pc('material_storage_kwh', Decimal('800.00'))

# Gesamtmaterial
material = inverter_cost + storage_cost + wallbox_cost
```

### 7. Rabatt (Komplett-Kit)

```python
discount = Decimal('0.00')

if not own_components:
    try:
        disc = PriceConfig.objects.get(price_type='discount_complete_kit')
        if disc.is_percentage:
            discount = (base_price * disc.value) / Decimal('100')
        else:
            discount = disc.value
    except PriceConfig.DoesNotExist:
        # Fallback: 15% Rabatt
        discount = (base_price * Decimal('0.15'))
```

### 8. Gesamtpreis

```python
total = base_price + travel_cost + surcharges + material - discount
```

---

## 📝 Beispiel-Requests & Responses

### Beispiel 1: Basis-Paket (kein Speicher, keine Wallbox)

**Request:**
```bash
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/" \
  -d "site_address=Hamburg" \
  -d "main_fuse_ampere=35" \
  -d "grid_type=3p" \
  -d "distance_meter_to_inverter=10" \
  -d "desired_power_kw=2.5" \
  -d "inverter_class=3kva" \
  -d "storage_kwh=0" \
  -d "has_wallbox=false" \
  -d "own_components=false"
```

**Response:**
```json
{
    "package": "basis",
    "basePrice": 890.0,
    "travelCost": 0.0,
    "surcharges": 0.0,
    "inverterCost": 1380.0,
    "storageCost": 0.0,
    "wallboxCost": 0.0,
    "materialCost": 1380.0,
    "discount": 133.5,
    "total": 2136.5
}
```

### Beispiel 2: Pro-Paket mit Wallbox

**Request:**
```bash
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/" \
  -d "site_address=Hamburg" \
  -d "main_fuse_ampere=35" \
  -d "grid_type=3p" \
  -d "distance_meter_to_inverter=20" \
  -d "desired_power_kw=6" \
  -d "inverter_class=5kva" \
  -d "storage_kwh=10" \
  -d "has_wallbox=true" \
  -d "wallbox_power=11kw" \
  -d "wallbox_mount=wall" \
  -d "wallbox_cable_installed=false" \
  -d "wallbox_cable_length=25" \
  -d "wallbox_pv_surplus=true" \
  -d "own_components=false"
```

**Response:**
```json
{
    "package": "pro",
    "basePrice": 2290.0,
    "travelCost": 0.0,
    "surcharges": 125.0,        // 5m WR-Kabel × 25€/m
    "inverterCost": 2750.0,
    "storageCost": 8000.0,
    "wallboxCost": 1790.0,      // 1290€ Base + 500€ Kabel
    "materialCost": 12540.0,
    "discount": 343.5,
    "total": 14611.5
}
```

---

## 🔐 API Security & Permissions

### CSRF-Exempt Endpoints

```python
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def pricing_preview(request):
    # Kann ohne CSRF-Token aufgerufen werden
    # Nützlich für Frontends ohne Session-Management
    pass
```

**Warum AllowAny?**
- Öffentlich zugänglicher Preisrechner
- Keine sensiblen Daten werden verarbeitet
- Nur Leseoperationen (keine DB-Änderungen)
- Rate-Limiting sollte in Production implementiert werden

---

## 🔗 Weitere API-Endpoints

### Create Precheck

**Endpoint:** `POST /api/precheck/`
**Status:** 🚧 Nicht implementiert (returns 501)

```python
@api_view(['POST'])
def create_precheck(request):
    return JsonResponse({'detail': 'not implemented'}, status=501)
```

**Geplante Funktionalität:**
- Speichert Precheck in DB
- Erstellt Customer + Site
- Triggert n8n-Workflow
- Sendet Bestätigungs-E-Mail

### Approve Quote

**Endpoint:** `POST /api/quotes/<pk>/approve/`
**Status:** 🚧 Nicht implementiert

**Geplante Funktionalität:**
- Setzt Quote-Status auf 'approved'
- Generiert PDF
- Sendet Angebot an Kunde

---

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)
**Siehe auch:**
- [CLAUDE_FRONTEND.md](CLAUDE_FRONTEND.md) - Frontend & JavaScript
- [CLAUDE_DATABASE.md](CLAUDE_DATABASE.md) - Datenbank & Migrationen
