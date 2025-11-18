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
# Helper-Funktion zum Abrufen von Preisen (Legacy)
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
```

> **Hinweis (seit 2025‑11‑11):** Die Precheck-Kalkulation nutzt `PriceConfig` nicht mehr direkt. Alle aktuell verwendeten Werte leben als Produkte mit den SKUs `PCHK-*` im Produktkatalog (siehe [CLAUDE_PRODUKTKATALOG.md](CLAUDE_PRODUKTKATALOG.md)). `PriceConfig` bleibt für alte Angebote und Admin-Views erhalten.

---

## �Y"T Precheck Pricing Engine (Product Catalog Driven)

**Datei:** `apps/quotes/pricing.py`

Die Live-Preisberechnung summiert klar definierte Bausteine aus dem Produktkatalog. Jeder Baustein hat eine SKU `PCHK-<KEY>` und lässt sich im Dashboard pflegen. Wichtige Gruppen:

| Baustein | Keys / Beispiele | Beschreibung |
|----------|------------------|--------------|
| Gebäude & Netz | `PCHK-BUILDING-EFH`, `PCHK-GRID-1P` | Feste Auf-/Abschläge je Gebäudetyp und Hausanschluss |
| Wechselrichter | `PCHK-INVERTER-TIER-3/5/10/20/30` | Pauschalen pro Leistungsbereich |
| Speicher | `PCHK-STORAGE-TIER-3/5/10` | Speicherstaffeln (optional) |
| WR-Kabel | `PCHK-WR-CABLE-PM-LT10/LT20/LT30` | Preis pro Meter basierend auf WR-Leistung |
| Wallbox | `PCHK-WALLBOX-BASE-*`, `PCHK-WALLBOX-CABLE-PM-*`, `PCHK-WALLBOX-MOUNT-STAND`, `PCHK-WALLBOX-PV-SURPLUS` | Basiskosten, Kabelmeter, Extras (Ständer, Überschussladen) |

`calculate_pricing()` liest die passenden Produkte, fasst sie zu Netto-/MwSt-/Bruttosummen zusammen und stellt jede Komponente in der API-Response dar. Neue/angepasste Preise bitte direkt über den Produktkatalog pflegen; Migration `0014_update_precheck_price_catalog.py` legt die Standardwerte an.

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
    "building_type": "mfh",                 # 'efh', 'mfh', 'commercial'
    "site_address": "Hamburg",              # optional – nur für spätere Auswertungen
    "main_fuse_ampere": 35,
    "grid_type": "1p",                      # '3p', '1p', 'tt'
    "distance_meter_to_inverter": 12,       # alternativ: distance_meter_to_hak

    # PV-System
    "desired_power_kw": 6,                  # bestimmt WR-Staffel + Kabelpreis
    "storage_kwh": 4,                       # 0 oder leer = kein Speicher
    "own_components": false,                # aktuell nur informativ

    # Wallbox (optional)
    "has_wallbox": true,
    "wallbox_power": "11kw",                # '4kw', '11kw', '22kw'
    "wallbox_mount": "stand",               # 'wall' oder 'stand'
    "wallbox_cable_installed": false,
    "wallbox_cable_length": 10,
    "wallbox_pv_surplus": true
}
```

### Response Format

```json
{
    "buildingSurcharge": 100.0,
    "gridSurcharge": 100.0,
    "inverterPrice": 1500.0,
    "storagePrice": 1300.0,
    "wrCableCost": 60.0,
    "wallboxBasePrice": 500.0,
    "wallboxCableCost": 140.0,
    "wallboxExtraCost": 400.0,
    "totalNet": 4100.0,
    "vatAmount": 779.0,
    "total": 4879.0
}
```

- Jeder Betrag entspricht genau einem PCHK-Produkt (siehe Tabelle oben).
- `totalNet` ist die Summe aller Bausteine, `vatAmount` = 19 % davon, `total` = Brutto.
- Es gibt keine Paket- oder Rabatt-Felder mehr; alles ist transparent nach Komponenten aufgeschlüsselt.

---

## 🧮 Preisberechnung-Logik (Detailliert)

Die aktuelle Engine besteht aus wenigen, transparenten Schritten – jede Stufe greift auf genau einen Produktdatensatz zurück:

1. **Gebäude & Netz**
   - uilding_type → PCHK-BUILDING-*
   - grid_type → PCHK-GRID-*

2. **Wechselrichter**
   - Leistung wird gerundet und einer Staffel (PCHK-INVERTER-TIER-*) zugeordnet.

3. **Speicher (optional)**
   - Falls storage_kwh > 0, wählt _storage_price die passende Staffel (PCHK-STORAGE-TIER-*).

4. **Kabelkosten WR**
   - Auf Basis der WR-Leistung wird der Meterpreis (PCHK-WR-CABLE-PM-LT*) gewählt und mit distance_meter_to_inverter multipliziert.

5. **Wallbox (optional)**
   - Basispreis (PCHK-WALLBOX-BASE-*), Kabelmeter (PCHK-WALLBOX-CABLE-PM-*) und Extras (Ständer/PV-Überschuss) werden separat addiert.

6. **Summen & MwSt.**
   - 	otalNet = Summe aller Komponenten
   - atAmount = totalNet * 0.19
   - 	otal = totalNet + vatAmount

Keine Rabatte, Pakete oder Travel-Zonen mehr – jeder Cent ist ein eigener Datensatz im Produktkatalog.

---

## ?? Beispiel-Requests & Responses

### Beispiel 1: Einfamilienhaus ohne Speicher/Wallbox

**Request:**
```bash
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/"
  -d "building_type=efh"
  -d "site_address=Hamburg"
  -d "main_fuse_ampere=35"
  -d "grid_type=3p"
  -d "distance_meter_to_inverter=8"
  -d "desired_power_kw=4"
  -d "storage_kwh=0"
  -d "has_wallbox=false"
```

**Response:**
```json
{
    "buildingSurcharge": 0.0,
    "gridSurcharge": 0.0,
    "inverterPrice": 1000.0,
    "storagePrice": 0.0,
    "wrCableCost": 40.0,
    "wallboxBasePrice": 0.0,
    "wallboxCableCost": 0.0,
    "wallboxExtraCost": 0.0,
    "totalNet": 1040.0,
    "vatAmount": 197.6,
    "total": 1237.6
}
```

### Beispiel 2: Mehrfamilienhaus mit Speicher & Wallbox

**Request:**
```bash
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/"
  -d "building_type=mfh"
  -d "site_address=Hamburg"
  -d "main_fuse_ampere=40"
  -d "grid_type=1p"
  -d "distance_meter_to_inverter=12"
  -d "desired_power_kw=6"
  -d "storage_kwh=4"
  -d "has_wallbox=true"
  -d "wallbox_power=11kw"
  -d "wallbox_mount=stand"
  -d "wallbox_cable_installed=false"
  -d "wallbox_cable_length=10"
  -d "wallbox_pv_surplus=true"
```

**Response:**
```json
{
    "buildingSurcharge": 100.0,
    "gridSurcharge": 100.0,
    "inverterPrice": 1500.0,
    "storagePrice": 1300.0,
    "wrCableCost": 60.0,
    "wallboxBasePrice": 500.0,
    "wallboxCableCost": 140.0,
    "wallboxExtraCost": 400.0,
    "totalNet": 4100.0,
    "vatAmount": 779.0,
    "total": 4879.0
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

## 🔌 N8n Integration API (v2.0.0 → v2.1.0)

**Datei:** `apps/integrations/api_views.py`

### Endpoint 1: Precheck-Daten abrufen

**URL:** `GET /api/integrations/precheck/<id>/`
**Permissions:** AllowAny (für interne Tests)
**Use Case:** N8n holt vollständige Precheck-Daten für KI-Validierung

**Response:**
```json
{
  "precheck_id": 123,
  "customer": {
    "id": 1,
    "name": "Max Mustermann",
    "email": "max@example.com",
    "phone": "+49 40 12345678"
  },
  "site": {
    "address": "Musterstraße 1, 20095 Hamburg",
    "building_type": "efh",
    "main_fuse_ampere": 35,
    "grid_type": "3p",
    "has_photos": true,
    "photo_count": 3,
    "photos": [
      {
        "id": 1,
        "category": "meter_cabinet",
        "url": "http://192.168.178.30:8025/media/precheck/meter.jpg"
      }
    ]
  },
  "project": {
    "desired_power_kw": 6.0,
    "storage_kwh": 5.0,
    "has_wallbox": true,
    "wallbox_power": "11kw",
    "customer_notes": "..."
  },
  "pricing": {
    "totalNet": 4100.00,
    "vatAmount": 779.00,
    "total": 4879.00
  },
  "completeness": {
    "has_customer_data": true,
    "has_customer_email": true,
    "has_site_photos": true,
    "has_meter_photo": true,
    "has_power_data": true,
    "has_pricing": true
  },
  "metadata": {
    "status": "pending",
    "created_at": "2025-11-18T14:30:00Z"
  }
}
```

**Features:**
- ✅ Automatisches Logging (WebhookLog)
- ✅ Completeness-Check für KI-Agent
- ✅ Absolute Foto-URLs
- ✅ Fehlerbehandlung (404 wenn Precheck nicht existiert)

### Endpoint 2: Pricing-Daten abrufen

**URL:** `GET /api/integrations/pricing/`
**Query-Parameter:**
- `categories`: Komma-separierte Kategorien (z.B. `?categories=Wechselrichter,Speicher`)
- `skus`: Komma-separierte SKUs (z.B. `?skus=PCHK-INVERTER-TIER-5`)
- `search`: Volltextsuche (z.B. `?search=Wallbox`)

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "sku": "PCHK-INVERTER-TIER-5",
      "name": "Wechselrichter 5kW Installation",
      "category": "Precheck-Artikel",
      "sales_price_net": 1500.00,
      "sales_price_gross": 1785.00,
      "vat_rate": 0.19,
      "unit": "Pauschal"
    }
  ],
  "count": 42,
  "filters_applied": {
    "categories": "Wechselrichter",
    "skus": "",
    "search": ""
  }
}
```

### Endpoint 3: Produktkategorien abrufen

**URL:** `GET /api/integrations/categories/`

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Precheck-Artikel",
      "description": "...",
      "product_count": 15
    }
  ],
  "count": 7
}
```

### Endpoint 4: Test-Webhook

**URL:** `POST /api/integrations/test/webhook/`
**Body:** Beliebige JSON-Daten

**Response:**
```json
{
  "status": "received",
  "message": "Webhook erfolgreich empfangen",
  "payload": {...},
  "webhook_log_id": 123,
  "timestamp": "2025-11-18T14:30:00Z"
}
```

**Use Case:** N8n-Verbindung testen

### Webhook-Signal: Precheck erstellt

**Trigger:** `post_save` Signal auf `Precheck` Model
**Ziel:** N8n Webhook-URL (aus `.env`)

**Payload:**
```json
{
  "event": "precheck_submitted",
  "precheck_id": 123,
  "api_base_url": "http://192.168.178.30:8025",
  "api_endpoints": {
    "precheck_data": "/api/integrations/precheck/123/",
    "pricing_data": "/api/integrations/pricing/"
  },
  "metadata": {
    "customer_email": "max@example.com",
    "has_customer": true,
    "has_site": true,
    "timestamp": "2025-11-18T14:30:00Z"
  }
}
```

**Logging:**
- Erstellt `WebhookLog` mit Status pending/success/failed
- Erstellt `N8nWorkflowStatus` für Tracking

**Fehlerbehandlung:**
- Timeout (10s)
- Connection Error
- HTTP Error
- Retry-Counter

### ⭐ Dashboard Integration (NEU v2.1.0)

**Zugriff:** `http://192.168.178.30:8025/dashboard/settings/n8n/`

#### N8n Einstellungen
- Editierbare Webhook URL (Datenbank überschreibt `.env`)
- API Key optional konfigurierbar
- Integration aktivieren/deaktivieren
- Statistik-Übersicht (Webhooks, Workflows)
- Copy-to-Clipboard für API-Endpoints

#### Webhook Test-Funktion
- Manueller Test mit Precheck-ID Input
- Sofortiges Feedback (Erfolg/Fehler mit Details)
- Test-Webhooks werden mit `test_mode: true` markiert
- Vollständiges Logging in WebhookLog

#### Webhook Logs Übersicht
- URL: `/dashboard/settings/n8n/webhook-logs/`
- Filter: Status, Richtung, Event Type, Zeitraum
- Detailansicht mit Payload & Response in Modal
- Paginierung (50 Logs pro Seite)

**Implementierung:**
- **Models:** `N8nConfiguration` (Singleton)
- **Forms:** `N8nConfigurationForm`, `WebhookTestForm`
- **Views:** `N8nSettingsView` (GET/POST), `WebhookLogListView`
- **Templates:** `n8n_settings.html`, `webhook_logs.html`

### Wichtige Bugfixes (v2.1.0)

**Problem:** `AttributeError: 'Precheck' object has no attribute 'customer'`

**Gelöst in:**
- `apps/core/dashboard_views.py:1837` (Test-Webhook)
- `apps/integrations/signals.py:58` (Automatischer Webhook)
- `apps/integrations/api_views.py:79-142` (API für N8n)

**Fix:** Precheck → Site → Customer Beziehung korrigiert
```python
# Alt (❌ Fehler)
precheck.customer.email

# Neu (✅ Funktioniert)
precheck.site.customer.email if (precheck.site and precheck.site.customer) else None
```

---

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)
**Siehe auch:**
- [N8N_INTEGRATION_PLAN.md](N8N_INTEGRATION_PLAN.md) - N8n Integration Details
- [CLAUDE_FRONTEND.md](CLAUDE_FRONTEND.md) - Frontend & JavaScript
- [CLAUDE_DATABASE.md](CLAUDE_DATABASE.md) - Datenbank & Migrationen
