# N8n-Integration: Implementierungsplan

**Status:** ✅ Phase 1 ABGESCHLOSSEN + Dashboard Integration (v2.1.0)
**Erstellt:** 2025-11-18
**Letzte Aktualisierung:** 2025-11-18 (v2.1.0)
**Projekt:** EDGARD Elektro PV-Service
**Architektur:** Django REST API ← → N8n (KI-gestützte Angebotserstellung)

---

## 🎯 Architektur-Übersicht

### Entscheidung: REST API statt direktem DB-Zugriff

**✅ GEWÄHLT: Django REST API als sichere Schnittstelle**

```
┌─────────────────────────────────────────────────────────────────┐
│                          ARCHITEKTUR                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  KUNDE                                                           │
│    │                                                             │
│    ↓ Füllt Precheck aus                                         │
│  DJANGO                                                          │
│    │ 1. Speichert in PostgreSQL                                 │
│    │ 2. Signal → Webhook an N8n                                 │
│    │                                                             │
│    ↓                                                             │
│  N8N (Workflow-Engine + KI)                                      │
│    │ 1. Empfängt Webhook mit Precheck-ID                        │
│    │ 2. Ruft Django API auf                                     │
│    │    GET /api/integrations/precheck/123/                     │
│    │    GET /api/integrations/pricing/                          │
│    │ 3. KI-Agent prüft Vollständigkeit                          │
│    │ 4. Entscheidung:                                           │
│    │    ├─ Vollständig → Angebot erstellen                      │
│    │    └─ Unvollständig → Kunde nachfragen                     │
│    │                                                             │
│    ↓                                                             │
│  DJANGO API (Callback)                                           │
│    │ POST /api/quotes/create-from-precheck/                     │
│    │ → Speichert Angebot                                        │
│    │ → Sendet E-Mail an Kunde                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Warum REST API statt direkter DB-Zugriff?

| Kriterium | Direkte DB | REST API (✅ Gewählt) |
|-----------|------------|----------------------|
| **Sicherheit** | ⚠️ DB-Passwort in N8n | ✅ API-Token (widerrufbar) |
| **Business Logic** | ❌ Umgangen | ✅ Integriert (Validierung, Signals) |
| **Schema-Änderungen** | ❌ Brechen N8n | ✅ API-Versionierung möglich |
| **Audit Logs** | ❌ Keine | ✅ Vollständig |
| **Testbarkeit** | ⚠️ Komplex | ✅ Einfach |
| **Wartbarkeit** | ❌ Schwierig | ✅ Einfach |

---

## ✅ Phase 1: Django Backend (ABGESCHLOSSEN + DASHBOARD)

### 1.1 Models erstellt

**Datei:** `apps/integrations/models.py`

#### WebhookLog Model
- Tracking aller Webhook-Calls (Django ↔ N8n)
- Status: pending, success, failed, retry
- Payload & Response als JSON
- Audit-Trail für Debugging

```python
class WebhookLog(models.Model):
    event_type = models.CharField(max_length=50, db_index=True)
    direction = models.CharField(
        max_length=10,
        choices=[('outgoing', 'Django → N8n'), ('incoming', 'N8n → Django')],
        default='outgoing',
    )
    status = models.CharField(
        max_length=20,
        choices=[('pending','pending'),('success','success'),('failed','failed'),('retry','retry')],
        default='pending',
        db_index=True,
    )
    payload = models.JSONField()
    response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    precheck_id = models.IntegerField(null=True, blank=True, db_index=True)
    quote_id = models.IntegerField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### N8nWorkflowStatus Model
- Status-Tracking pro Precheck/Quote
- KI-Validierung-Ergebnisse
- Workflow-Metadaten

```python
class N8nWorkflowStatus(models.Model):
    STATUS_CHOICES = [
        ('initiated', 'Workflow gestartet'),
        ('data_validation', 'Daten werden validiert'),
        ('incomplete', 'Daten unvollstaendig'),
        ('waiting_customer', 'Wartet auf Kundenantwort'),
        ('generating_quote', 'Angebot wird erstellt'),
        ('quote_ready', 'Angebot fertig'),
        ('sent_to_customer', 'An Kunde versendet'),
        ('failed', 'Fehler aufgetreten'),
    ]

    precheck = models.ForeignKey(
        'quotes.Precheck',
        on_delete=models.CASCADE,
        related_name='workflow_statuses',
        null=True,
        blank=True,
    )
    quote = models.ForeignKey(
        'quotes.Quote',
        on_delete=models.CASCADE,
        related_name='workflow_statuses',
        null=True,
        blank=True,
    )
    workflow_id = models.CharField(max_length=100, blank=True)  # N8n Execution ID
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='initiated', db_index=True)
    ai_validation_result = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_event_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
```

#### N8nConfiguration Model (⭐ NEU - v2.1.0)
- **Singleton-Model** für Webhook-URL und API-Key
- Datenbank-Konfiguration überschreibt `.env` Werte
- Cache-Optimierung (5 Minuten)
- Editierbar über Dashboard

```python
class N8nConfiguration(models.Model):
    webhook_url = models.URLField(max_length=500, blank=True)
    api_key = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_webhook_url(cls):
        """DB hat Priorität vor .env"""
        config = cls.get_config()
        return config.webhook_url or settings.N8N_WEBHOOK_URL
```

**Features:**
- ✅ Singleton-Pattern (nur 1 Config erlaubt)
- ✅ Automatisches Fallback auf `.env`
- ✅ Cache-Invalidierung bei Änderungen
- ✅ Kann nicht gelöscht werden

### 1.2 API-Endpoints erstellt

**Datei:** `apps/integrations/api_views.py`

#### 1. GET /api/integrations/precheck/<id>/
Liefert alle Daten eines Prechecks für N8n.

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
    "photos": [...]
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
    "total": 4879.00,
    "breakdown": {...}
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
- ✅ Vollständige Kundendaten
- ✅ Fotos mit absoluten URLs
- ✅ Preisberechnung
- ✅ **Completeness-Check** für KI-Validierung
- ✅ Automatisches Logging (WebhookLog)

#### 2. GET /api/integrations/pricing/
Liefert Preisdaten aus Produktkatalog.

**Query-Parameter:**
- `categories`: Filter nach Kategorien (komma-separiert)
- `skus`: Filter nach SKUs (komma-separiert)
- `search`: Volltextsuche

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
      "vat_rate": 0.19,
      "sales_price_gross": 1785.00,
      "unit": "Pauschal"
    },
    ...
  ],
  "count": 42
}
```

**Beispiel-Aufrufe:**
```bash
# Alle Precheck-Artikel
GET /api/integrations/pricing/?categories=Precheck-Artikel

# Spezifische SKUs
GET /api/integrations/pricing/?skus=PCHK-INVERTER-TIER-5,PCHK-STORAGE-TIER-3

# Suche
GET /api/integrations/pricing/?search=Wallbox
```

#### 3. GET /api/integrations/categories/
Liefert alle Produktkategorien.

#### 4. POST /api/integrations/test/webhook/
Test-Endpoint zum Testen der Verbindung.

### 1.3 Signal-Handler erstellt

**Datei:** `apps/integrations/signals.py`

**Trigger:** `post_save` auf `Precheck` Model

**Workflow:**
1. Neuer Precheck wird erstellt
2. Signal feuert automatisch
3. Webhook an N8n mit minimalen Daten (nur ID)
4. N8n holt Rest via API

```python
@receiver(post_save, sender=Precheck)
def precheck_submitted_handler(sender, instance, created, **kwargs):
    """
    Sendet Webhook an N8n wenn neuer Precheck erstellt wird.
    """
    if not created:
        return

    payload = {
        'event': 'precheck_submitted',
        'precheck_id': instance.id,
        'api_endpoints': {
            'precheck_data': f'/api/integrations/precheck/{instance.id}/',
            'pricing_data': '/api/integrations/pricing/',
        },
        'metadata': {...}
    }

    # Webhook-Log erstellen
    webhook_log = WebhookLog.objects.create(...)

    # Workflow-Status erstellen
    workflow_status = N8nWorkflowStatus.objects.create(...)

    # Webhook senden
    response = requests.post(settings.N8N_WEBHOOK_URL, json=payload)

    # Erfolg/Fehler loggen
    webhook_log.mark_success() / webhook_log.mark_failed()
```

**Features:**
- ✅ Automatischer Trigger bei neuem Precheck
- ✅ Fehlerbehandlung (Timeout, Connection Error, HTTP Error)
- ✅ Retry-Logik vorbereitet
- ✅ Vollständiges Logging

### 1.4 URLs registriert

**Datei:** `apps/integrations/urls.py`

```python
urlpatterns = [
    path('precheck/<int:precheck_id>/', get_precheck_data),
    path('pricing/', get_pricing_data),
    path('categories/', get_product_categories),
    path('test/webhook/', test_webhook_receiver),
]
```

**Eingebunden in:** `edgard_site/urls.py`
```python
path('api/integrations/', include('apps.integrations.urls')),
```

**Verfügbare URLs:**
- `http://192.168.178.30:8025/api/integrations/precheck/123/`
- `http://192.168.178.30:8025/api/integrations/pricing/`
- `http://192.168.178.30:8025/api/integrations/categories/`
- `http://192.168.178.30:8025/api/integrations/test/webhook/`

### 1.5 Admin-Interface erstellt

**Datei:** `apps/integrations/admin.py`

**Features:**
- ✅ WebhookLog mit farbigen Status-Badges
- ✅ N8nWorkflowStatus mit Timeline-Ansicht
- ✅ Filter & Suche
- ✅ JSON-Anzeige für Payload/Response

**Zugriff:**
`http://192.168.178.30:8025/admin/integrations/`

### 1.6 Konfiguration

**Datei:** `.env`

```bash
# N8n Integration
N8N_WEBHOOK_URL=http://localhost:5678/webhook/precheck-submitted
N8N_API_KEY=
BASE_URL=http://192.168.178.30:8025
```

**Datei:** `edgard_site/settings.py`

```python
N8N_WEBHOOK_URL = config('N8N_WEBHOOK_URL', default='')
N8N_API_KEY = config('N8N_API_KEY', default='')
BASE_URL = config('BASE_URL', default='http://192.168.178.30:8025')
```

### 1.7 Dashboard Integration (⭐ NEU - v2.1.0)

**Zugriff:** `http://192.168.178.30:8025/dashboard/settings/n8n/`

#### Features

**1. Editierbare N8n Konfiguration**
- Webhook URL direkt im Dashboard änderbar (ohne .env-Zugriff)
- API Key optional konfigurierbar
- Integration aktivieren/deaktivieren per Checkbox
- Datenbank-Werte überschreiben `.env` automatisch

**2. Webhook Test-Funktion**
- Manueller Test mit beliebiger Precheck-ID
- Sofortiges Feedback (Erfolg/Fehler mit Details)
- Test-Webhooks werden mit `test_mode: true` markiert
- Vollständiges Logging in WebhookLog

**3. Statistik-Übersicht**
- Gesamtzahl Webhooks (Heute, 7 Tage, Gesamt)
- Status-Verteilung (Erfolgreich, Fehlgeschlagen, Ausstehend)
- Workflow-Statistiken (Aktiv, Abgeschlossen, Fehlgeschlagen)
- Letzte 10 Webhook-Aktivitäten

**4. Webhook Logs Übersicht**
- Zugriff: `http://192.168.178.30:8025/dashboard/settings/n8n/webhook-logs/`
- Filter nach Status, Richtung, Event Type, Zeitraum
- Detailansicht mit Payload & Response
- Paginierung (50 Logs pro Seite)

#### Implementierte Dateien

**Forms:** `apps/integrations/forms.py`
```python
class N8nConfigurationForm(forms.ModelForm):
    """Formular für Webhook URL & API Key"""

class WebhookTestForm(forms.Form):
    """Formular für manuellen Webhook-Test"""
    precheck_id = forms.IntegerField()
```

**Views:** `apps/core/dashboard_views.py`
```python
class N8nSettingsView(LoginRequiredMixin, View):
    """POST: Speichere Config oder sende Test-Webhook"""

class WebhookLogListView(LoginRequiredMixin, ListView):
    """Liste aller Webhook-Logs mit Filtern"""
```

**Templates:**
- `templates/dashboard/n8n_settings.html` - Konfiguration & Test
- `templates/dashboard/webhook_logs.html` - Log-Übersicht

**Navigation:** Sidebar → Einstellungen → N8n Integration

#### Wichtige Bugfixes (v2.1.0)

**Problem:** `AttributeError: 'Precheck' object has no attribute 'customer'`

**Ursache:** Precheck hat keine direkte `customer` Beziehung.
Korrekte Struktur: **Precheck → Site → Customer**

**Gelöst in:**
- `apps/core/dashboard_views.py` (Test-Webhook)
- `apps/integrations/signals.py` (Automatischer Webhook)
- `apps/integrations/api_views.py` (API für N8n)

**Alt:**
```python
precheck.customer.email  # ❌ AttributeError
```

**Neu:**
```python
precheck.site.customer.email if (precheck.site and precheck.site.customer) else None  # ✅
```

Alle Customer-Zugriffe wurden mit defensiven Checks versehen.

---

## 🚀 Phase 2: N8n Setup (NÄCHSTE SCHRITTE)

### 2.1 N8n Installation

**Option A: Docker (empfohlen)**
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

**Option B: NPM**
```bash
npm install -g n8n
n8n start
```

**Zugriff:** `http://localhost:5678`

### 2.2 Workflow 1: Precheck-Datenvalidierung

```
[Webhook Trigger]
  ↓
  Empfängt: { precheck_id: 123, api_endpoints: {...} }
  ↓
[HTTP Request Node]
  ↓
  GET http://192.168.178.30:8025/api/integrations/precheck/123/
  ↓
[HTTP Request Node]
  ↓
  GET http://192.168.178.30:8025/api/integrations/pricing/
  ↓
[OpenAI/Claude Node] - KI-Validierung
  ↓
  Prompt: "Prüfe Vollständigkeit dieser PV-Anfrage..."
  ↓
  Response: { complete: true/false, missing_data: [...], confidence: 0.95 }
  ↓
[IF Node] - complete?
  ↓                        ↓
  JA                       NEIN
  ↓                        ↓
[Workflow 2]              [Email Node]
Angebot erstellen         Nachfrage an Kunde
```

### 2.3 KI-Prompt (Beispiel)

```
System: Du bist ein Experte für PV-Anlagen-Installationen.

User:
Prüfe diese Kundenanfrage auf Vollständigkeit:

Kundendaten:
- Name: {{ $json.customer.name }}
- Email: {{ $json.customer.email }}
- Telefon: {{ $json.customer.phone }}

Standort:
- Adresse: {{ $json.site.address }}
- Gebäudetyp: {{ $json.site.building_type }}
- Hauptsicherung: {{ $json.site.main_fuse_ampere }} A
- Netzform: {{ $json.site.grid_type }}

Projekt:
- WR-Leistung: {{ $json.project.desired_power_kw }} kW
- Speicher: {{ $json.project.storage_kwh }} kWh
- Wallbox: {{ $json.project.has_wallbox }}

Fotos:
- Anzahl: {{ $json.site.photo_count }}
- Zählerkasten-Foto: {{ $json.completeness.has_meter_photo }}
- HAK-Foto: {{ $json.completeness.has_hak_photo }}

Fragen:
1. Sind alle notwendigen Daten für ein qualifiziertes Angebot vorhanden?
2. Welche Daten fehlen?
3. Gibt es Unstimmigkeiten?
4. Welche Fragen sollten wir stellen?

Antwort als JSON:
{
  "complete": boolean,
  "missing_data": [array of strings],
  "plausibility_issues": [array],
  "recommended_questions": [array],
  "confidence_score": number (0-1)
}
```

### 2.4 Workflow 2: Angebotserstellung

```
[Webhook Trigger / IF-Node aus Workflow 1]
  ↓
[HTTP Request] - Quote in Django erstellen
  ↓
  POST http://192.168.178.30:8025/api/quotes/create-from-precheck/
  Body: { precheck_id: 123 }
  ↓
[OpenAI/Claude Node] - Angebots-Text generieren
  ↓
  Prompt: "Erstelle professionellen Angebots-Text für..."
  ↓
[PDF Generator Node]
  ↓
  HTML → PDF (Gotenberg, WeasyPrint, oder N8n-PDF-Node)
  ↓
[Email Node]
  ↓
  An: {{ $json.customer.email }}
  Betreff: "Ihr PV-Angebot von EDGARD Elektro"
  Anhang: angebot.pdf
```

### 2.5 Workflow 3: Nachfrage bei Unvollständigkeit

```
[Email Node]
  ↓
  An: {{ $json.customer.email }}
  Betreff: "Rückfrage zu Ihrer PV-Anfrage"
  ↓
  Text:
  Guten Tag {{ $json.customer.name }},

  vielen Dank für Ihre Anfrage. Für ein qualifiziertes Angebot
  benötigen wir noch folgende Informationen:

  {% for item in $json.ai_validation.missing_data %}
  - {{ item }}
  {% endfor %}

  Bitte ergänzen Sie diese Daten hier: {{ $json.update_link }}

  Mit freundlichen Grüßen
  EDGARD Elektro Team
```

---

## 📊 Testing-Checkliste

### Phase 1 (Django Backend) - ✅ ABGESCHLOSSEN (inkl. Dashboard v2.1.0)

- [x] Models erstellt (WebhookLog, N8nWorkflowStatus, N8nConfiguration)
- [x] Migrations erstellt (0001_initial, 0002_n8nconfiguration)
- [x] API-Endpoints implementiert
  - [x] GET /api/integrations/precheck/<id>/
  - [x] GET /api/integrations/pricing/
  - [x] GET /api/integrations/categories/
  - [x] POST /api/integrations/test/webhook/
- [x] Signal-Handler registriert (mit N8nConfiguration)
- [x] URLs konfiguriert
- [x] Admin-Interface erstellt (WebhookLog, N8nWorkflowStatus, N8nConfiguration)
- [x] .env Konfiguration
- [x] **⭐ Dashboard Integration (NEU v2.1.0)**
  - [x] N8n Settings View mit editierbarer Config
  - [x] Webhook Test-Funktion mit Precheck-ID Input
  - [x] Webhook Logs Übersicht mit Filtern
  - [x] Statistik-Übersicht (Webhooks, Workflows)
  - [x] Forms (N8nConfigurationForm, WebhookTestForm)
  - [x] Templates (n8n_settings.html, webhook_logs.html)
- [x] **Bugfixes (v2.1.0)**
  - [x] Customer-Access-Fix (Precheck → Site → Customer)
  - [x] Defensive Checks in allen 3 Dateien

### Phase 2 (N8n Setup) - 🚧 TODO

- [ ] N8n installieren
- [ ] Webhook-URL in .env konfigurieren
- [ ] Test-Webhook senden
- [ ] Workflow 1 erstellen (Datenvalidierung)
- [ ] KI-Provider konfigurieren (OpenAI/Claude)
- [ ] Workflow 2 erstellen (Angebotserstellung)
- [ ] Workflow 3 erstellen (Nachfrage)
- [ ] PDF-Generierung testen
- [ ] E-Mail-Versand konfigurieren
- [ ] End-to-End-Test

---

## 🧪 Manuelle Tests

### Test 1: API-Endpoints testen

```bash
# Precheck-Daten abrufen
curl http://192.168.178.30:8025/api/integrations/precheck/1/

# Preisdaten abrufen
curl http://192.168.178.30:8025/api/integrations/pricing/

# Test-Webhook senden
curl -X POST http://192.168.178.30:8025/api/integrations/test/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "source": "manual"}'
```

### Test 2: Webhook von N8n simulieren

```bash
# Precheck erstellen über Preisrechner
# → Signal feuert automatisch
# → Webhook-Log im Admin prüfen
```

---

## 🔐 Sicherheit (Für Production)

### TODO: API-Key-Authentifizierung hinzufügen

**Aktuell:** AllowAny (nur für interne Tests!)

**Für Production:**

```python
# apps/integrations/authentication.py

class N8nAPIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('X-API-KEY')
        if api_key != settings.N8N_API_KEY:
            raise AuthenticationFailed('Invalid API Key')
        return (AnonymousUser(), None)

# In api_views.py
@authentication_classes([N8nAPIKeyAuthentication])
@permission_classes([IsAuthenticated])
def get_precheck_data(request, precheck_id):
    ...
```

**N8n HTTP Request Node Configuration:**
```json
{
  "method": "GET",
  "url": "http://192.168.178.30:8025/api/integrations/precheck/123/",
  "headers": {
    "X-API-KEY": "{{ $credentials.djangoApiKey }}"
  }
}
```

---

## 📚 Weitere Dokumentation

- **[CLAUDE_API.md](CLAUDE_API.md)** - API-Endpoints Details
- **[CLAUDE_DATABASE.md](CLAUDE_DATABASE.md)** - Datenbank-Schema
- **[CLAUDE.md](CLAUDE.md)** - Hauptdokumentation

---

## 🎯 Nächste Schritte

### Sofort möglich:

1. **Migrationen ausführen**
   ```bash
   python manage.py makemigrations integrations
   python manage.py migrate
   ```

2. **API testen**
   ```bash
   # Precheck erstellen über Preisrechner
   http://192.168.178.30:8025/precheck/

   # API-Endpoint testen
   curl http://192.168.178.30:8025/api/integrations/precheck/1/
   ```

3. **Admin-Interface prüfen**
   ```
   http://192.168.178.30:8025/admin/integrations/webhooklog/
   http://192.168.178.30:8025/admin/integrations/n8nworkflowstatus/
   ```

### Nächste Phase:

4. **N8n installieren**
5. **Webhook-URL konfigurieren**
6. **Ersten Workflow erstellen**
7. **KI-Provider anbinden**

---

**Letzte Aktualisierung:** 2025-11-18
**Status:** ✅ Phase 1 abgeschlossen - Bereit für N8n Integration
**Nächstes Review:** Nach N8n-Setup
