# CLAUDE_ADMIN.md - Admin-Dashboard Dokumentation

> Vollständige Dokumentation des modernen Admin-Dashboards für EDGARD Elektro PV-Service

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)

---

## 📋 Übersicht

**Version:** 1.0.0 (2025-01-09)
**Status:** ✅ VOLLSTÄNDIG IMPLEMENTIERT
**URL:** http://192.168.178.30:8025/dashboard/
**Design:** Modern & Minimalistisch (Desktop-only)

### Hauptfunktionen

- ✅ **Dashboard Übersicht** mit Echtzeit-Statistiken
- ✅ **Precheck-Verwaltung** mit Suche, Filter & Export
- ✅ **Preiskonfiguration** mit Inline-Editing
- ✅ **Kundenverwaltung** mit Detailansichten
- ✅ **Angebotsverwaltung** mit Status-Tracking
- ✅ **CSV-Export** für alle Hauptbereiche
- ✅ **Login-Schutz** für alle Admin-Seiten

---

## 🚀 Erste Schritte

### 1. Server starten

```bash
cd "E:\ANPR\PV-Service"
python manage.py runserver 192.168.178.30:8025
```

### 2. Admin-Dashboard aufrufen

```
URL: http://192.168.178.30:8025/dashboard/
```

### 3. Login

**WICHTIG:** Nur eingeloggte Benutzer haben Zugriff auf das Dashboard.

```bash
# Superuser erstellen (falls noch nicht vorhanden)
python manage.py createsuperuser

# Username, E-Mail und Passwort eingeben
```

**Login-URL:** http://192.168.178.30:8025/admin/login/

---

## 📁 Projekt-Struktur

### Neue Dateien

```
E:\ANPR\PV-Service\
├── apps/core/
│   ├── dashboard_urls.py          # ✅ Dashboard URL-Konfiguration
│   ├── dashboard_views.py         # ✅ 10 Class-Based Views
│   └── forms.py                   # ✅ Django Forms
│
├── templates/dashboard/
│   ├── base.html                  # ✅ Base-Template mit Sidebar
│   ├── home.html                  # ✅ Dashboard Startseite
│   ├── precheck_list.html         # ✅ Precheck-Liste
│   ├── precheck_detail.html       # ✅ Precheck-Details
│   ├── price_list.html            # ✅ Preiskonfiguration
│   ├── customer_list.html         # ✅ Kundenliste
│   ├── customer_detail.html       # ✅ Kundendetails
│   ├── quote_list.html            # ✅ Angebotsliste
│   └── quote_detail.html          # ✅ Angebotsdetails
│
└── docs/
    └── CLAUDE_ADMIN.md            # ✅ Diese Dokumentation
```

### Geänderte Dateien

```
edgard_site/urls.py                # ✅ Dashboard-URLs eingebunden
```

---

## 🔗 URL-Struktur

### Übersicht

| URL | View | Beschreibung | Template |
|-----|------|--------------|----------|
| `/dashboard/` | DashboardHomeView | Übersicht & Statistiken | home.html |
| `/dashboard/prechecks/` | PrecheckListView | Precheck-Liste | precheck_list.html |
| `/dashboard/prechecks/<id>/` | PrecheckDetailView | Precheck-Details | precheck_detail.html |
| `/dashboard/prechecks/export/` | PrecheckExportView | CSV-Export | - |
| `/dashboard/prices/` | PriceConfigListView | Preise verwalten | price_list.html |
| `/dashboard/prices/<id>/edit/` | PriceConfigUpdateView | Preis bearbeiten | - |
| `/dashboard/customers/` | CustomerListView | Kundenliste | customer_list.html |
| `/dashboard/customers/<id>/` | CustomerDetailView | Kundendetails | customer_detail.html |
| `/dashboard/quotes/` | QuoteListView | Angebotsliste | quote_list.html |
| `/dashboard/quotes/<id>/` | QuoteDetailView | Angebotsdetails | quote_detail.html |

### App-Name: `dashboard`

```python
# In Templates verwenden:
{% url 'dashboard:home' %}
{% url 'dashboard:precheck_list' %}
{% url 'dashboard:precheck_detail' pk=precheck.id %}
```

---

## 🎨 Design & UI

### Farbschema

```css
:root {
    --primary-blue: #2563eb;      /* Hauptfarbe (Buttons, Links) */
    --primary-green: #10b981;     /* Erfolg */
    --primary-dark: #1e293b;      /* Dunkle Elemente */

    --neutral-50: #f8fafc;        /* Hintergrund */
    --neutral-100: #f1f5f9;       /* Cards */
    --neutral-200: #e2e8f0;       /* Borders */
    --neutral-600: #475569;       /* Text */
    --neutral-800: #1e293b;       /* Headlines */

    --status-success: #10b981;    /* Grün */
    --status-warning: #f59e0b;    /* Orange */
    --status-error: #ef4444;      /* Rot */
    --status-info: #3b82f6;       /* Blau */
}
```

### Layout

```
┌────────────┬──────────────────────────────────────┐
│  SIDEBAR   │  MAIN CONTENT                        │
│  (240px)   │                                      │
│            │  ┌──── Breadcrumbs ─────┐            │
│ Logo       │  │ Dashboard > Prechecks │            │
│            │  └──────────────────────┘            │
│ Übersicht  │                                      │
│ Prechecks  │  [Page Content]                      │
│ Preise     │                                      │
│ Kunden     │                                      │
│ Angebote   │                                      │
│            │                                      │
│ [Logout]   │                                      │
└────────────┴──────────────────────────────────────┘
```

### Komponenten

#### Statistik-Cards

```html
<div class="stat-card">
    <div class="stat-icon">
        <i class="fas fa-clipboard-check"></i>
    </div>
    <div class="stat-content">
        <div class="stat-label">Prechecks heute</div>
        <div class="stat-value">7</div>
        <div class="stat-change text-success">
            <i class="fas fa-arrow-up"></i> +2 vs. gestern
        </div>
    </div>
</div>
```

#### Status-Badges

```html
<span class="badge badge-success">Neu</span>
<span class="badge badge-info">Versendet</span>
<span class="badge badge-warning">In Prüfung</span>
<span class="badge badge-danger">Abgelehnt</span>
```

---

## 📊 Views-Dokumentation

### 1. DashboardHomeView

**URL:** `/dashboard/`
**Template:** `dashboard/home.html`
**Typ:** TemplateView

**Context-Daten:**
```python
{
    'stats': {
        'prechecks_total': 45,
        'prechecks_week': 12,
        'prechecks_today': 3,
        'quotes_total': 28,
        'quotes_sent': 15,
        'customers_total': 34,
        'revenue_month': Decimal('45320.50')
    },
    'recent_prechecks': QuerySet[Precheck] (Top 5),
    'recent_quotes': QuerySet[Quote] (Top 5)
}
```

**Features:**
- Echtzeit-Statistiken
- Trend-Indikatoren (+/- vs. gestern/Woche)
- Neueste Anfragen (Top 5)
- Quick Actions

---

### 2. PrecheckListView

**URL:** `/dashboard/prechecks/`
**Template:** `dashboard/precheck_list.html`
**Typ:** ListView

**Query-Parameter:**
- `q` - Suchbegriff (Name, E-Mail, Adresse)
- `power_min` - Mindest-Leistung (kW)
- `power_max` - Maximal-Leistung (kW)
- `has_storage` - Nur mit Speicher
- `has_wallbox` - Nur mit Wallbox
- `own_components` - Nur mit eigenen Komponenten

**Beispiel:**
```
/dashboard/prechecks/?q=Müller&has_wallbox=true&power_min=5
```

**Features:**
- Suche über Kunde, E-Mail, Adresse, Notizen
- Filter nach Leistung, Speicher, Wallbox
- Pagination (25 pro Seite)
- Sortierung nach Datum
- CSV-Export-Button

**Optimierung:**
```python
queryset = Precheck.objects.select_related(
    'site__customer'
).prefetch_related('quote_set')
```

---

### 3. PrecheckDetailView

**URL:** `/dashboard/prechecks/<id>/`
**Template:** `dashboard/precheck_detail.html`
**Typ:** DetailView

**Context-Daten:**
```python
{
    'precheck': Precheck,
    'customer': Customer,
    'site': Site,
    'quote': Quote (falls vorhanden),
    'uploads': [
        ('Zählerschrank', ImageFieldFile),
        ('Hausanschlusskasten', ImageFieldFile),
        ('Montageorte', ImageFieldFile),
        ('Kabelwege', ImageFieldFile)
    ]
}
```

**Features:**
- Vollständige Precheck-Daten
- Kundeninformationen
- PV-System-Spezifikationen
- Wallbox-Konfiguration (falls vorhanden)
- Foto-Galerie mit Lightbox
- Quick Actions (E-Mail, Anrufen, PDF)

---

### 4. PrecheckExportView

**URL:** `/dashboard/prechecks/export/`
**Typ:** View (CSV-Download)

**Response:**
```
Content-Type: text/csv; charset=utf-8-sig
Content-Disposition: attachment; filename="prechecks_20250109_1430.csv"
```

**CSV-Spalten:**
```
ID;Datum;Kunde;E-Mail;Telefon;Adresse;Leistung (kW);Speicher (kWh);Wallbox;Eigene Komponenten;Notizen
```

**Encoding:** UTF-8 mit BOM (für Excel-Kompatibilität)

---

### 5. PriceConfigListView

**URL:** `/dashboard/prices/`
**Template:** `dashboard/price_list.html`
**Typ:** ListView

**Context-Daten:**
```python
{
    'prices_grouped': {
        'travel': [PriceConfig, ...],      # Anfahrtskosten
        'surcharges': [PriceConfig, ...],  # Zuschläge
        'packages': [PriceConfig, ...],    # Pakete
        'materials': [PriceConfig, ...],   # Material
        'wallbox': [PriceConfig, ...],     # Wallbox
        'cables': [PriceConfig, ...]       # Kabel
    }
}
```

**Features:**
- Gruppierte Darstellung nach Kategorien
- Inline-Editing mit AJAX
- Enter = Speichern, Escape = Abbrechen
- Live-Updates ohne Page-Reload
- Success/Error Messages

**JavaScript-Funktionen:**
```javascript
enableEdit(row)       // Edit-Mode aktivieren
savePrice(row)        // AJAX-Save
cancelEdit(row)       // Abbrechen
```

---

### 6. PriceConfigUpdateView

**URL:** `/dashboard/prices/<id>/edit/`
**Typ:** UpdateView
**Form:** PriceConfigForm

**Editierbare Felder:**
- `value` - Preis (Decimal, 2 Nachkommastellen)
- `is_percentage` - Prozentangabe? (Boolean)
- `description` - Beschreibung (max 200 Zeichen)

**Read-Only:**
- `price_type` - Typ (nicht änderbar)

**Validierung:**
```python
# value muss positiv sein
if value < 0:
    raise ValidationError("Preis muss positiv sein")

# Prozentangabe: 0-100%
if is_percentage and (value < 0 or value > 100):
    raise ValidationError("Prozentsatz muss zwischen 0 und 100 liegen")
```

**Success-Message:**
```
Preis "Wallbox Installation 11kW" erfolgreich aktualisiert.
```

---

### 7. CustomerListView

**URL:** `/dashboard/customers/`
**Template:** `dashboard/customer_list.html`
**Typ:** ListView

**Query-Parameter:**
- `q` - Suchbegriff (Name, E-Mail, Telefon, Adresse)
- `customer_type` - Filter nach Typ (private/business)

**Features:**
- Suche über Name, E-Mail, Telefon
- Filter nach Kundentyp
- Aggregation: Anzahl Sites & Prechecks
- Pagination (25 pro Seite)
- CSV-Export

**Statistiken im Context:**
```python
{
    'total_customers': 45,
    'private_customers': 38,
    'business_customers': 7
}
```

---

### 8. CustomerDetailView

**URL:** `/dashboard/customers/<id>/`
**Template:** `dashboard/customer_detail.html`
**Typ:** DetailView

**Context-Daten:**
```python
{
    'customer': Customer,
    'sites': QuerySet[Site],
    'prechecks': QuerySet[Precheck],
    'quotes': QuerySet[Quote]
}
```

**Features:**
- Vollständige Kundendaten
- DSGVO Consent-Status
- Liste aller Standorte
- Liste aller Prechecks
- Liste aller Angebote
- Quick Actions (E-Mail, Anrufen)

---

### 9. QuoteListView

**URL:** `/dashboard/quotes/`
**Template:** `dashboard/quote_list.html`
**Typ:** ListView

**Query-Parameter:**
- `q` - Suchbegriff (Angebotsnummer, Kunde)
- `status` - Filter nach Status

**Features:**
- Suche nach Angebotsnummer, Kunde
- Filter nach Status
- Farbcodierte Status-Badges
- Pagination (25 pro Seite)
- CSV-Export

**Status-Choices:**
```python
STATUS_CHOICES = [
    ('draft', 'Entwurf'),
    ('review', 'In Prüfung'),
    ('approved', 'Freigegeben'),
    ('sent', 'Versendet'),
    ('accepted', 'Angenommen'),
    ('rejected', 'Abgelehnt'),
    ('expired', 'Abgelaufen')
]
```

---

### 10. QuoteDetailView

**URL:** `/dashboard/quotes/<id>/`
**Template:** `dashboard/quote_detail.html`
**Typ:** DetailView

**Context-Daten:**
```python
{
    'quote': Quote,
    'precheck': Precheck,
    'customer': Customer,
    'site': Site,
    'items': QuerySet[QuoteItem]
}
```

**Features:**
- Angebotsdaten komplett
- Kunde & Precheck
- Alle Positionen (QuoteItems)
- Preisberechnung (Netto, MwSt, Brutto)
- Status-Änderung
- PDF Download
- Quick Actions

---

## 🔐 Sicherheit & Permissions

### LoginRequiredMixin

Alle Views sind geschützt:

```python
class DashboardHomeView(LoginRequiredMixin, TemplateView):
    login_url = '/admin/login/'
    ...
```

**Unautorisierter Zugriff:**
```
/dashboard/ → Redirect zu /admin/login/?next=/dashboard/
```

### CSRF-Protection

Alle Forms sind geschützt:

```html
<form method="post">
    {% csrf_token %}
    ...
</form>
```

### SQL-Injection-Schutz

Django ORM verhindert SQL-Injection:

```python
# Sicher (ORM)
Precheck.objects.filter(site__customer__name__icontains=query)

# NIEMALS (Raw SQL mit User-Input)
cursor.execute(f"SELECT * FROM precheck WHERE name='{query}'")  # ❌
```

---

## 📈 Performance-Optimierungen

### Query-Optimierung

**Problem:** N+1 Queries

```python
# ❌ SCHLECHT (N+1 Problem)
for precheck in Precheck.objects.all():
    print(precheck.site.customer.name)  # Extra Query pro Precheck!
```

**Lösung:** select_related

```python
# ✅ GUT (nur 1 Query)
prechecks = Precheck.objects.select_related('site__customer')
for precheck in prechecks:
    print(precheck.site.customer.name)
```

### Pagination

Alle List-Views verwenden Pagination:

```python
paginate_by = 25  # 25 Einträge pro Seite
```

### Aggregation

Statistiken werden effizient berechnet:

```python
Customer.objects.annotate(
    sites_count=Count('sites'),
    prechecks_count=Count('sites__precheck')
)
```

---

## 🔧 Häufige Aufgaben

### Preise aktualisieren

**Option 1: Django Admin**
```
http://192.168.178.30:8025/admin/quotes/priceconfig/
```

**Option 2: Dashboard (Inline-Edit)**
```
http://192.168.178.30:8025/dashboard/prices/
→ Auf Zeile klicken → Preis ändern → Enter
```

**Option 3: Django Shell**
```bash
python manage.py shell

from apps.quotes.models import PriceConfig
from decimal import Decimal

# Einzelnen Preis ändern
price = PriceConfig.objects.get(price_type='wallbox_base_11kw')
price.value = Decimal('1390.00')
price.save()
```

### CSV-Export erstellen

**Prechecks exportieren:**
```
http://192.168.178.30:8025/dashboard/prechecks/
→ [Export CSV] Button
```

**Dateiname:**
```
prechecks_20250109_1430.csv
```

**Encoding:** UTF-8 mit BOM (Excel-kompatibel)

### Kunden suchen

**In Dashboard:**
```
http://192.168.178.30:8025/dashboard/customers/?q=Müller
```

**In Django Shell:**
```python
from apps.customers.models import Customer

# Name suchen
customers = Customer.objects.filter(name__icontains='Müller')

# E-Mail suchen
customers = Customer.objects.filter(email__icontains='beispiel.de')
```

---

## 🐛 Troubleshooting

### Problem: "Permission denied" beim Zugriff auf /dashboard/

**Ursache:** Nicht eingeloggt

**Lösung:**
```
1. Gehe zu http://192.168.178.30:8025/admin/login/
2. Logge dich mit Superuser-Credentials ein
3. Gehe zurück zu /dashboard/
```

### Problem: "DoesNotExist: PriceConfig matching query does not exist"

**Ursache:** Preiskonfiguration nicht migriert/geseeded

**Lösung:**
```bash
python manage.py migrate
python manage.py shell

from apps.quotes.models import PriceConfig
PriceConfig.objects.count()  # Sollte 25 sein
```

Falls 0:
```bash
# Migration 0006 erneut ausführen
python manage.py migrate quotes 0005
python manage.py migrate quotes 0006
```

### Problem: "No such table: quotes_precheck"

**Ursache:** Datenbank nicht migriert

**Lösung:**
```bash
python manage.py migrate
```

### Problem: CSV-Export zeigt Umlaute falsch an

**Ursache:** Excel erkennt UTF-8 nicht

**Lösung:** In PrecheckExportView ist bereits UTF-8 BOM implementiert:
```python
response.write('\ufeff')  # UTF-8 BOM
```

Falls Problem weiterhin besteht:
1. Excel öffnen
2. Daten → Aus Text/CSV
3. Dateiursprung: Unicode (UTF-8)
4. Trennzeichen: Semikolon

---

## 📚 Weiterführende Dokumentation

- [CLAUDE.md](CLAUDE.md) - Hauptdokumentation
- [CLAUDE_API.md](CLAUDE_API.md) - API-Endpoints
- [CLAUDE_FRONTEND.md](CLAUDE_FRONTEND.md) - Frontend (Preisrechner)
- [CLAUDE_DATABASE.md](CLAUDE_DATABASE.md) - Datenbank & Migrationen
- [CLAUDE_DEPLOYMENT.md](CLAUDE_DEPLOYMENT.md) - Deployment & Testing

---

## 🎯 Nächste Schritte (Optional)

### Phase 1: Features erweitern
- [ ] PDF-Generierung für Angebote
- [ ] E-Mail-Versand aus Dashboard
- [ ] Bulk-Aktionen (mehrere Prechecks gleichzeitig bearbeiten)
- [ ] Erweiterte Filteroptionen
- [ ] Exportformate (Excel, JSON)

### Phase 2: UX-Verbesserungen
- [ ] Dark Mode Toggle
- [ ] Tastatur-Shortcuts
- [ ] Drag & Drop für Uploads
- [ ] Inline-Editing für mehr Felder
- [ ] Auto-Save

### Phase 3: Analytics
- [ ] Dashboard-Charts (Chart.js)
- [ ] Umsatz-Diagramme
- [ ] Conversion-Tracking
- [ ] Monats-/Jahres-Reports

### Phase 4: Automatisierung
- [ ] Automatische Status-Änderungen
- [ ] E-Mail-Benachrichtigungen
- [ ] Reminder für auslaufende Angebote
- [ ] Workflow-Automatisierung

---

**Status:** ✅ PRODUKTIONSBEREIT
**Letztes Update:** 2025-01-09
**Version:** 1.0.0

**Für Fragen zur Admin-Oberfläche, siehe diese Dokumentation.**
