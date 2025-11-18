# EDGARD -- Elektro PV-Service Projekt

## 📋 Projektübersicht

**EDGARD Elektro** - Professionelle Django-Website für PV-Anlagen Elektroinstallationsservice in Hamburg mit automatisierter Angebotserstellung und Live-Preisberechnung.

**Status:** ✅ VOLL FUNKTIONSFÄHIG + WALLBOX + PRODUKTKATALOG + ANGEBOTS-BEARBEITUNG
**Version:** 1.3.0 (2025-01-16)
**Live-URL (Dev):** http://192.168.178.30:8025/precheck/

---

## 🚀 Quick Start

### Server starten
```bash
cd "E:\ANPR\PV-Service"
python manage.py runserver 192.168.178.30:8025
```

### Wichtige URLs
- Preisrechner: http://192.168.178.30:8025/precheck/
- Django Admin: http://192.168.178.30:8025/admin/
- API Pricing: http://192.168.178.30:8025/api/pricing/preview/

---

## 📁 Projektstruktur (Übersicht)

```
E:\ANPR\PV-Service\
├── docs/
│   ├── CLAUDE.md                       # Diese Datei - Hauptdokumentation
│   ├── CLAUDE_API.md                   # API & Backend Details
│   ├── CLAUDE_FRONTEND.md              # Frontend & JavaScript
│   ├── CLAUDE_DATABASE.md              # Datenbank & Migrationen
│   ├── CLAUDE_ADMIN.md                 # Admin-Dashboard
│   ├── CLAUDE_PRODUKTKATALOG.md        # Produktkatalog-System
│   ├── CLAUDE_QUOTE_EDITING.md         # ⭐ NEU: Angebots-Bearbeitung
│   └── CLAUDE_DEPLOYMENT.md            # Deployment & Testing
│
├── manage.py
├── requirements.txt
├── create_test_products.py             # ⭐ NEU: Test-Daten für Produktkatalog
├── edgard_site/                        # Django Project
├── apps/
│   ├── quotes/                         # ⭐ Hauptapp: Pricing, Precheck, Products
│   │   ├── models.py                   # PriceConfig, Quote, Precheck, ProductCategory, Product
│   │   ├── api_views.py                # pricing_preview API
│   │   └── migrations/
│   │       ├── 0006_seed_wallbox_pricing.py
│   │       ├── 0010_productcategory_product.py
│   │       ├── 0020_add_location_choices.py     # ⭐ NEU: Precheck Choices
│   │       ├── 0021_alter_precheck_storage_location.py
│   │       ├── 0022_add_quote_notes.py          # ⭐ NEU: Quote.notes
│   │       └── 0023_add_quoteitem_vat_rate.py   # ⭐ NEU: QuoteItem.vat_rate
│   ├── core/                           # User, Customer, Site, Dashboard
│   │   ├── dashboard_views.py          # +8 Produktkatalog + ⭐ NEU: QuoteEditView, ProductAutocompleteView
│   │   ├── dashboard_urls.py           # ⭐ NEU: /quotes/<pk>/edit/, /api/products/autocomplete/
│   │   └── forms.py                    # ⭐ NEU: QuoteEditForm, QuoteItemForm, QuoteItemFormSet
│   ├── customers/
│   ├── inventory/
│   └── ...
├── templates/
│   ├── quotes/
│   │   └── precheck_wizard.html        # 6-Schritte Preisrechner
│   └── dashboard/                      # Admin-Dashboard
│       ├── base.html                   # Mit Produktkatalog-Navigation
│       ├── category_list.html          # Kategorienliste
│       ├── category_form.html
│       ├── product_list.html           # Produktliste
│       ├── product_form.html
│       ├── quote_edit.html             # ⭐ NEU: Angebots-Bearbeitung (720 Zeilen)
│       ├── quote_detail.html           # ⭐ NEU: "Bearbeiten" Button
│       ├── precheck_list.html          # Mit Bootstrap Delete-Modal
│       ├── precheck_detail.html        # ⭐ NEU: get_FOO_display() für Locations
│       ├── customer_list.html          # Mit Bootstrap Delete-Modal
│       └── ...
└── static/
```

---

## 🎯 Kern-Features

### ✅ Implementiert:
- **6-Schritte Preisrechner** mit Live-Preisberechnung
- **Wallbox-Integration** (3 Leistungsklassen: 4kW, 11kW, 22kW)
- **Variable Kabelpreise** abhängig von WR/Wallbox-Leistung
- **Database-Driven Pricing** (25 PriceConfig-Einträge)
- **Produktkatalog-System** (v1.2.0)
  - 7 Kategorien (Precheck, Wechselrichter, Speicher, etc.)
  - 30+ Produkte mit EK/VK-Preisen
  - Automatische Brutto-Berechnung & Margen
  - Filter, Suche, Pagination
  - Bootstrap Delete-Modals mit CASCADE-Warnungen
- **Angebots-Bearbeitungssystem** (⭐ NEU v1.3.0)
  - Positionen hinzufügen/bearbeiten/löschen
  - Produktkatalog-Autocomplete mit Tastatursteuerung
  - Individuelle MwSt.-Sätze pro Position
  - Echtzeit-Berechnung & Split-MwSt.-Anzeige
  - Automatische Positionsnummerierung
  - Django Inline-Formsets
- **Precheck-Formular Optimierungen** (⭐ NEU v1.3.0)
  - Location-Felder mit CHOICES validiert
  - Automatische Label-Anzeige (get_FOO_display)
  - Validierungsfehler-Handling verbessert
- **Enter-Taste Navigation** (springt zum nächsten Feld)
- **3-Punkte Progress-Bar** (Standort → PV-System → Preis) mit zentrierten Labels dank gemeinsamer Flex-Spalten
- **LocalStorage Persistierung** (Daten überleben Page-Reload)
- **Responsive Design** mit Bootstrap 5 + Glassmorphism

### 🔥 Nächste Schritte:
1. n8n-Integration für Workflow-Automatisierung
2. PDF-Generierung (WeasyPrint)
3. E-Mail-Templates & Versand
4. File-Upload Backend (S3)

---

## 💡 Quick Reference für KI-Agenten

### Projekt-Typ
- **Framework:** Django 4.2 (Monolith)
- **Frontend:** Multi-Step-Form (kein SPA Framework)
- **API:** DRF mit AllowAny permissions für öffentliche Endpoints
- **Database:** PostgreSQL (Production) / SQLite (Dev)

### Wichtigste Dateien
| Datei | Zweck |
|-------|-------|
| `apps/quotes/api_views.py` | Backend-Logik für Preisberechnung |
| `apps/quotes/pricing.py` | Zentrale Pricing-Engine (Wizard/API/Quotes) |
| `apps/quotes/models.py` | PriceConfig Model mit 25 PRICE_TYPES |
| `templates/quotes/precheck_wizard.html` | Frontend + JavaScript |
| `apps/quotes/migrations/0006_seed_wallbox_pricing.py` | Wallbox-Preise seeden |

### Wenn du Preise ändern musst:
```python
# Django Admin verwenden
http://your-domain/admin/quotes/priceconfig/

# Oder in Django Shell:
from apps.quotes.models import PriceConfig
config = PriceConfig.objects.get(price_type='wallbox_base_11kw')
config.value = Decimal('1390.00')
config.save()
```

### Wenn du neue Features hinzufügen musst:
1. **Model erweitern** → `apps/quotes/models.py`
2. **Migration erstellen** → `python manage.py makemigrations`
3. **Migration ausführen** → `python manage.py migrate`
4. **API erweitern** → `apps/quotes/api_views.py` (pricing_preview)
5. **Frontend erweitern** → `templates/quotes/precheck_wizard.html`
6. **Zusammenfassung aktualisieren** → `updateSummary()` Funktion

---

## 📚 Detaillierte Dokumentation

Für tiefere Einblicke in spezifische Bereiche, siehe:

- **[CLAUDE_API.md](CLAUDE_API.md)** - API-Endpoints, Preisberechnung-Logik, PriceConfig Model
- **[CLAUDE_FRONTEND.md](CLAUDE_FRONTEND.md)** - HTML-Struktur, JavaScript-Funktionen, CSS
- **[CLAUDE_DATABASE.md](CLAUDE_DATABASE.md)** - Models, Migrationen, Schema
- **[CLAUDE_ADMIN.md](CLAUDE_ADMIN.md)** - Admin-Dashboard Views & Templates
- **[CLAUDE_PRODUKTKATALOG.md](CLAUDE_PRODUKTKATALOG.md)** - Produktkatalog-System & Delete-Modals
- **[CLAUDE_QUOTE_EDITING.md](CLAUDE_QUOTE_EDITING.md)** - ⭐ NEU: Angebots-Bearbeitung mit Autocomplete
- **[CLAUDE_DEPLOYMENT.md](CLAUDE_DEPLOYMENT.md)** - Deployment, Testing, Known Issues

---

## 🔧 Häufige Befehle

### Development
```bash
# Server starten
python manage.py runserver 192.168.178.30:8025

# Migrationen erstellen & ausführen
python manage.py makemigrations
python manage.py migrate

# Django Shell
python manage.py shell

# Superuser erstellen
python manage.py createsuperuser
```

### Testing
```bash
# API testen (Basis-Anfrage)
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/" \
  -d "site_address=Hamburg" \
  -d "main_fuse_ampere=35" \
  -d "grid_type=3p" \
  -d "desired_power_kw=4" \
  -d "has_wallbox=false"

# API testen (Mit Wallbox)
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/" \
  -d "site_address=Hamburg" \
  -d "has_wallbox=true" \
  -d "wallbox_power=11kw" \
  -d "wallbox_cable_length=25"
```

---

## 📊 Preisberechnung (Kurzübersicht)
- Wizard, API und Angebotserstellung nutzen alle die zentrale Pricing-Engine (`apps/quotes/pricing.py`). Sie liefert Netto-/Brutto-Werte auf Basis der `PriceConfig`.
- Das Formularfeld „Wechselrichter-Klasse" wurde entfernt; die Klasse wird intern über `desired_power_kw` abgeleitet.
- Die Success-Seite zeigt denselben Brutto-Gesamtpreis wie der Live-Preis (inkl. MwSt. und zwei Nachkommastellen).

### Paket-Bestimmung
```python
if storage_kwh > 0:
    package = 'pro'        # 2.290€
elif desired_power > 3 or grid_type == 'TT':
    package = 'plus'       # 1.490€
else:
    package = 'basis'      # 890€
```

### Wallbox-Preise
- **4kW Installation:** 890€
- **11kW Installation:** 1.290€
- **22kW Installation:** 1.690€
- **Ständer-Montage:** +350€
- **Kabel:** 12-30€/m (je nach Leistung)

### Anfahrtskosten (ortbasiert)
- Hamburg: 0€
- bis 30km: 50€
- bis 60km: 95€

→ Siehe [CLAUDE_API.md](CLAUDE_API.md) für detaillierte Logik

---

## 🎨 Website-Seiten

| URL | Beschreibung | Status |
|-----|--------------|--------|
| `/` | Homepage mit Hero-Section | ✅ |
| `/precheck/` | 6-Schritte Preisrechner | ✅ |
| `/precheck/success/` | Erfolgsseite | ✅ |
| `/faq/` | FAQ zu PV-Anlagen | ✅ |
| `/packages/` | Leistungspakete | ✅ |
| `/compatible-systems/` | Kompatible WR/Speicher | ✅ |
| `/admin/` | Django Admin | ✅ |

---

## 📦 Dependencies (Kurzübersicht)

### Backend
```
Django==4.2.26
djangorestframework==3.15.2
psycopg[binary]==3.2.12
python-decouple==3.8
```

### Frontend (CDN)
- Bootstrap 5.1.3
- Font Awesome 6.4.0

→ Siehe [CLAUDE_DEPLOYMENT.md](CLAUDE_DEPLOYMENT.md) für vollständige Liste

---

## 🐛 Known Issues (Top 3)

1. **Virtual Env Dependencies:** Manuell installieren mit `pip install -r requirements.txt`
2. **Migration Conflicts:** Bei Problemen `0003` als Basis verwenden
3. **Enter-Key Submit:** Verhindert durch `e.preventDefault()` in setupValidation()

→ Siehe [CLAUDE_DEPLOYMENT.md](CLAUDE_DEPLOYMENT.md) für Lösungen

---

## 📝 Letzte Änderungen

### Version 2.1.0 (2025-11-18) - N8n Dashboard Integration

✅ **Dashboard Integration für N8n:**
- N8n Einstellungs-Seite mit editierbarer Webhook URL
- API Key Konfiguration direkt im Dashboard
- Webhook Test-Funktion mit Precheck-ID Input
- Statistik-Übersicht (Webhooks: Heute, 7 Tage, Gesamt)
- Workflow-Statistiken (Aktiv, Abgeschlossen, Fehlgeschlagen)
- Webhook Logs mit Filter & Detailansicht
- Navigation: Sidebar → Einstellungen → N8n Integration

✅ **Neue Models & Migrations:**
- N8nConfiguration Model (Singleton-Pattern)
- Migration 0002_n8nconfiguration
- Datenbank-Config überschreibt `.env` automatisch
- Cache-Optimierung (5 Minuten)

✅ **Neue Forms & Views:**
- N8nConfigurationForm, WebhookTestForm
- N8nSettingsView (GET/POST)
- WebhookLogListView (mit Filtern)
- 2 neue Templates (n8n_settings.html, webhook_logs.html)

✅ **Wichtige Bugfixes:**
- Customer-Access-Fix: Precheck → Site → Customer
- Defensive Checks in 3 Dateien (dashboard_views, signals, api_views)
- AttributeError behoben: `precheck.customer.email` → `precheck.site.customer.email`

**URLs:**
- `/dashboard/settings/n8n/` - Einstellungen & Test
- `/dashboard/settings/n8n/webhook-logs/` - Log-Übersicht

### Version 1.3.0 (2025-01-16)

✅ **Angebots-Bearbeitungssystem (NEU):**
- 2 neue Views: QuoteEditView, ProductAutocompleteView
- 3 neue Forms: QuoteEditForm, QuoteItemForm, QuoteItemFormSet
- Template quote_edit.html (720 Zeilen mit JavaScript)
- Produktkatalog-Autocomplete mit Debouncing (300ms)
- Tastatursteuerung (↑↓ Enter Escape)
- Echtzeit-Berechnung aller Summen
- Split-MwSt.-Anzeige bei unterschiedlichen Sätzen
- Automatische Positionsnummerierung
- Dynamische Zeilen hinzufügen/löschen

✅ **Model-Erweiterungen:**
- Migration 0022: Quote.notes TextField
- Migration 0023: QuoteItem.vat_rate DecimalField
- Individuelle MwSt.-Sätze pro Position (19%, 7%, 0%)
- Interne Notizen für Kundenwünsche

✅ **Precheck-Formular Fixes:**
- Migration 0020: INVERTER_LOCATION_CHOICES hinzugefügt
- Migration 0021: 'same_as_inverter' zu STORAGE_LOCATION_CHOICES
- CharField → ChoiceField für inverter_location/storage_location
- get_FOO_display() in Templates für deutsche Labels
- Verbesserte Validierungsfehler-Behandlung

✅ **UI-Optimierungen:**
- Quote Detail: "Bearbeiten" Button hinzugefügt
- Kompakte rechte Spalte (col-lg-3 statt col-lg-4)
- Reduzierte Textgrößen (Labels: 12px, Hilfetext: 10px)
- .compact-form CSS-Klasse für platzsparende Formulare

### Version 1.2.0 (2025-01-11)

✅ **Produktkatalog-System:**
- 2 neue Models: ProductCategory, Product
- Migration 0010 erstellt & angewendet
- 8 neue Views (Category & Product CRUD)
- 4 neue Templates (kompakte 11-Spalten-Tabelle)
- Test-Daten-Script mit 30 Produkten
- Automatische Brutto-Berechnung & Margen

✅ **Bootstrap Delete-Modals:**
- Professionelle Lösch-Bestätigungen für alle Bereiche
- CASCADE-Warnungen bei Customer/Precheck-Deletion
- PROTECT-Warnungen bei Category-Deletion
- Rot-gelbe Warnfarben für bessere UX

✅ **Dashboard-Erweiterungen:**
- Sidebar mit Produktkatalog-Navigation
- Filter & Suche für Produkte
- Inline-Editing vorbereitet
- CSV-Export-Buttons

### Version 1.1.0 (2025-01-08)

✅ **Wallbox-Integration komplett:**
- 11 neue PriceConfig-Einträge
- Variable Kabelpreise (WR & Wallbox)
- Frontend-Felder in Schritt 1 & 2
- API-Berechnung erweitert

---

**Für weitere Details, siehe die spezialisierten Dokumentationsdateien:**
- [CLAUDE_API.md](CLAUDE_API.md)
- [CLAUDE_FRONTEND.md](CLAUDE_FRONTEND.md)
- [CLAUDE_DATABASE.md](CLAUDE_DATABASE.md)
- [CLAUDE_DEPLOYMENT.md](CLAUDE_DEPLOYMENT.md)
