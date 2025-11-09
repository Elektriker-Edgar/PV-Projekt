# CLAUDE_DEPLOYMENT.md - Deployment & Testing

> Deployment-Checkliste, Testing-Prozeduren und Known Issues

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)

---

## 📦 Dependencies

### Python Packages (requirements.txt)

```txt
Django==4.2.26
djangorestframework==3.15.2
django-cors-headers==4.4.0
django-extensions==3.2.3
django-debug-toolbar==4.4.6
celery==5.5.3
redis==6.1.1
psycopg[binary]==3.2.12
python-decouple==3.8
pillow==10.4.0
```

### Frontend Libraries (CDN)

```html
<!-- Bootstrap 5.1.3 -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>

<!-- Font Awesome 6.4.0 -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
```

---

## 🚀 Deployment-Checkliste

### 1. Environment Setup

#### Development

```bash
# Virtual Environment erstellen
python -m venv venv

# Aktivieren (Windows)
venv\Scripts\activate

# Aktivieren (Linux/Mac)
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

#### Production

```bash
# .env Datei erstellen
cat > .env << EOL
SECRET_KEY=<generate-new-secret-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=pv_service_prod
DB_USER=<db-user>
DB_PASSWORD=<db-password>
DB_HOST=<db-host>
DB_PORT=5432

CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
EOL
```

### 2. Database Setup

```bash
# Migrationen ausführen
python manage.py migrate

# Superuser erstellen
python manage.py createsuperuser

# PriceConfig-Werte überprüfen
python manage.py shell
>>> from apps.quotes.models import PriceConfig
>>> PriceConfig.objects.count()  # Sollte 25 sein
>>> exit()
```

### 3. Static Files

```bash
# Development (nicht nötig, DEBUG=True serviert automatisch)
# Production:
python manage.py collectstatic --noinput
```

### 4. Server starten

#### Development

```bash
python manage.py runserver 192.168.178.30:8025
```

#### Production (Gunicorn)

```bash
# Installation
pip install gunicorn

# Starten
gunicorn edgard_site.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Mit Systemd Service
sudo systemctl start pv-service
sudo systemctl enable pv-service
```

#### Production (Nginx + Gunicorn)

**Nginx Config:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

### 5. Security Checklist

- [ ] `DEBUG=False` in Production
- [ ] `SECRET_KEY` neu generieren und geheim halten
- [ ] `ALLOWED_HOSTS` konfigurieren
- [ ] `CSRF_TRUSTED_ORIGINS` konfigurieren
- [ ] `CORS_ALLOWED_ORIGINS` konfigurieren
- [ ] HTTPS aktivieren (Let's Encrypt)
- [ ] Rate-Limiting für API-Endpoints implementieren
- [ ] File-Upload Validierung aktivieren
- [ ] Database Backups einrichten

---

## 🧪 Testing

### Manuelle Tests: Preisrechner-Workflow

#### Testfall 1: Basis-Paket (kein Speicher, keine Wallbox)

```
Schritt 1:
- Gebäudetyp: Einfamilienhaus
- Baujahr: 2010
- Hauptsicherung: 35A
- Netzart: 3-Phasen
- Distanz Zähler→WR: 10m
- Wallbox: NEIN

Schritt 2:
- Gewünschte Leistung: 2.5kW
- Speicher: 0kWh

Erwartetes Ergebnis:
- Paket: Basis (890€)
- Anfahrt: 0€ (Hamburg)
- Zuschläge: 0€
- Material: ~1.380€
- Rabatt: ~133€
- GESAMT: ~2.137€
```

#### Testfall 2: Plus-Paket (>3kW, kein Speicher)

```
Schritt 1: (wie Testfall 1)
Schritt 2:
- Gewünschte Leistung: 5kW
- Speicher: 0kWh

Erwartetes Ergebnis:
- Paket: Plus (1.490€)
- Material: ~2.750€ (inkl. SPD + Meter)
- GESAMT: ~3.985€
```

#### Testfall 3: Pro-Paket (mit Speicher + Wallbox)

```
Schritt 1:
- Distanz Zähler→WR: 20m
- Wallbox: JA

Schritt 2:
- Gewünschte Leistung: 6kW
- Speicher: 10kWh
- Wallbox Leistung: 11kW
- Wallbox Montage: Wand
- Kabel nicht verlegt: 25m

Erwartetes Ergebnis:
- Paket: Pro (2.290€)
- Zuschläge: 125€ (5m WR-Kabel × 25€/m)
- Material: ~12.540€
  - WR: 2.750€
  - Speicher: 8.000€ (10kWh × 800€/kWh)
  - Wallbox: 1.790€ (1.290€ Base + 500€ Kabel)
- Rabatt: ~343€
- GESAMT: ~14.612€
```

#### Testfall 4: Enter-Navigation

```
Vorgehen:
1. Formular öffnen
2. In erstes Feld klicken
3. Wert eingeben
4. Enter drücken → Sollte zum nächsten Feld springen
5. In jedem Feld wiederholen
6. Letztes Feld: Enter sollte NICHT submitten

Erwartetes Verhalten:
- Fokus springt zum nächsten sichtbaren Feld
- Keine Seite-Neuladen
- Funktioniert nur in aktuellem Schritt
```

#### Testfall 5: LocalStorage Persistenz

```
Vorgehen:
1. Formular teilweise ausfüllen (Schritt 1 & 2)
2. Browser-Tab neu laden (F5)
3. Prüfen: Felder sollten befüllt sein

Erwartetes Verhalten:
- Alle Werte bleiben erhalten
- Auch Checkboxen/Selects
- Preis-Daten bleiben gespeichert
```

### API-Tests (curl)

#### Test 1: Basis-Anfrage

```bash
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/" \
  -d "site_address=Hamburg" \
  -d "main_fuse_ampere=35" \
  -d "grid_type=3p" \
  -d "distance_meter_to_inverter=10" \
  -d "desired_power_kw=4" \
  -d "storage_kwh=0" \
  -d "has_wallbox=false" \
  -d "own_components=false"
```

**Erwartete Response:**
```json
{
    "package": "plus",
    "basePrice": 1490.0,
    "travelCost": 0.0,
    "surcharges": 0.0,
    "inverterCost": 2750.0,
    "storageCost": 0.0,
    "wallboxCost": 0.0,
    "materialCost": 2750.0,
    "discount": 223.5,
    "total": 4016.5
}
```

#### Test 2: Mit Wallbox

```bash
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/" \
  -d "site_address=Hamburg" \
  -d "main_fuse_ampere=35" \
  -d "grid_type=3p" \
  -d "distance_meter_to_inverter=20" \
  -d "desired_power_kw=6" \
  -d "storage_kwh=10" \
  -d "has_wallbox=true" \
  -d "wallbox_power=11kw" \
  -d "wallbox_mount=wall" \
  -d "wallbox_cable_installed=false" \
  -d "wallbox_cable_length=25" \
  -d "wallbox_pv_surplus=true" \
  -d "own_components=false"
```

**Erwartete Response:**
```json
{
    "package": "pro",
    "basePrice": 2290.0,
    "travelCost": 0.0,
    "surcharges": 125.0,
    "inverterCost": 2750.0,
    "storageCost": 8000.0,
    "wallboxCost": 1790.0,
    "materialCost": 12540.0,
    "discount": 343.5,
    "total": 14611.5
}
```

#### Test 3: Fehlerfall (fehlende Parameter)

```bash
curl -X POST "http://192.168.178.30:8025/api/pricing/preview/" \
  -d "site_address=Hamburg"
```

**Erwartete Response:** 400 Bad Request oder Default-Preise

---

## 🐛 Known Issues & Workarounds

### Issue 1: Virtual Environment Dependencies

**Problem:**
```
ModuleNotFoundError: No module named 'django'
```

**Ursache:** `venv` hatte nicht alle Dependencies installiert

**Lösung:**
```bash
# Alle Packages manuell installieren
pip install django djangorestframework django-cors-headers
pip install django-extensions celery redis
pip install django-debug-toolbar psycopg[binary]
pip install python-decouple pillow
```

**Oder:**
```bash
pip install -r requirements.txt
```

---

### Issue 2: psycopg2-binary Compilation Error

**Problem:**
```
error: Microsoft Visual C++ 14.0 or greater is required.
Building wheel for psycopg2-binary failed
```

**Ursache:** psycopg2-binary benötigt C++-Compiler zum Kompilieren

**Lösung:**
```bash
# Verwende psycopg[binary] statt psycopg2-binary
pip uninstall psycopg2-binary
pip install psycopg[binary]
```

**Alternative (wenn Problem weiterhin besteht):**
```bash
# Windows: Visual C++ Build Tools installieren
# https://visualstudio.microsoft.com/downloads/
# Dann:
pip install psycopg2-binary
```

---

### Issue 3: Migration Dependency Conflict

**Problem:**
```
django.db.migrations.exceptions.NodeNotFoundError:
Migration quotes.0005_alter_priceconfig_price_type depends on
nonexistent node ('quotes', '0004_add_wallbox_pricing')
```

**Ursache:** Migration 0004 existierte in DB, aber nicht mehr im Code

**Lösung:**
```python
# 1. Migration 0005 Dependencies ändern
# apps/quotes/migrations/0005_alter_priceconfig_price_type.py

dependencies = [
    ('quotes', '0003_seed_price_config_and_components'),  # Statt 0004
]

# 2. Neue Migration 0006 für Wallbox-Seeding erstellen
python manage.py makemigrations --empty quotes --name seed_wallbox_pricing

# 3. Migration ausführen
python manage.py migrate
```

**Best Practice:**
- **NIE** Migrationen aus Code löschen, wenn sie in DB angewendet wurden
- Bei Problemen: Neue Migration erstellen statt alte zu ändern
- Immer Reverse-Funktionen implementieren

---

### Issue 4: Enter-Key Submit (GELÖST)

**Problem:**
```
Beim Drücken der Enter-Taste in einem Input-Feld wurde das Formular
submittet und die Seite neu geladen. Alle Daten gingen verloren.
```

**Ursache:** Browser-Default-Verhalten bei Forms

**Lösung:**
```javascript
form.addEventListener('keydown', function(e) {
    if(e.key === 'Enter' &&
       e.target.tagName !== 'TEXTAREA' &&
       e.target.type !== 'submit' &&
       e.target.tagName !== 'BUTTON') {

        e.preventDefault();  // Verhindert Submit

        // Intelligentes Springen zum nächsten Feld
        const inputs = Array.from(form.querySelectorAll(
            'input:not([type=hidden]):not([type=file]),select,textarea'
        ));
        const visibleInputs = inputs.filter(input => {
            const step = input.closest('.step-content');
            return step && step.classList.contains('active') &&
                   !input.disabled && input.offsetParent !== null;
        });

        const currentIndex = visibleInputs.indexOf(e.target);
        if(currentIndex > -1 && currentIndex < visibleInputs.length - 1) {
            visibleInputs[currentIndex + 1].focus();
        }
    }
});
```

**Status:** ✅ GELÖST seit v1.1.0

---

### Issue 5: Zusammenfassung leer (GELÖST)

**Problem:**
```
In Schritt 5 zeigte die Zusammenfassung nur Bindestriche (-) an.
Alle Felder waren leer.
```

**Ursache:** `updateSummary()` wurde VOR dem Schritt-Wechsel aufgerufen

**Falsch:**
```javascript
function nextStep() {
    if(currentStep === 5) updateSummary();  // Zu früh!
    currentStep++;
    // ...
}
```

**Richtig:**
```javascript
function nextStep() {
    currentStep++;
    if(currentStep === 5) updateSummary();  // Nach dem Wechsel!
    // ...
}
```

**Status:** ✅ GELÖST seit v1.1.0

---

### Issue 6: Progress-Labels nicht zentriert (GELÖST)

**Problem:**
```
Progress-Bar Labels waren nicht perfekt unter den Punkten zentriert.
```

**Lösung:**
```css
.step-label {
    position: absolute;
    transform: translateX(-50%);  /* Zentriert horizontal */
    white-space: nowrap;
}

.step-label:nth-child(1) { left: 0%; }
.step-label:nth-child(2) { left: 50%; }
.step-label:nth-child(3) { left: 100%; }
```

**Status:** ✅ GELÖST seit v1.1.0

---

## 📊 Performance-Optimierungen (Zukünftig)

### Database Indexing

```python
# apps/quotes/models.py
class PriceConfig(models.Model):
    price_type = models.CharField(max_length=50, unique=True, db_index=True)
    # ...

    class Meta:
        indexes = [
            models.Index(fields=['price_type']),
        ]
```

### API Caching

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 Minuten
@api_view(['POST'])
def pricing_preview(request):
    # ...
```

### Rate Limiting

```python
from rest_framework.throttling import AnonRateThrottle

class PricingRateThrottle(AnonRateThrottle):
    rate = '100/hour'

@api_view(['POST'])
@throttle_classes([PricingRateThrottle])
def pricing_preview(request):
    # ...
```

---

## 🔍 Debugging

### Django Debug Toolbar aktivieren

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', '192.168.178.30']
```

### Logging konfigurieren

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.quotes': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### SQL Queries debuggen

```python
from django.db import connection

# Nach API-Call:
print(len(connection.queries))  # Anzahl Queries
for q in connection.queries:
    print(q['sql'])
```

---

## 🎯 Nächste Entwicklungsschritte

### 🔥 Hohe Priorität

1. **n8n-Integration**
   - Webhook für Precheck-Submissions
   - Automatische Lead-Qualifizierung
   - E-Mail-Benachrichtigungen an Team

2. **PDF-Generierung (WeasyPrint)**
   - Angebots-PDF mit Breakdown
   - Logo und Branding
   - Download-Link in Success-Seite

3. **E-Mail-Templates**
   - Bestätigung an Kunde
   - Benachrichtigung an Team
   - Follow-Up-Sequenz

4. **File-Upload Backend**
   - S3 Integration
   - Bildkomprimierung
   - Thumbnail-Generierung

### 🟡 Mittlere Priorität

5. **Rechtliche Seiten**
   - Impressum
   - Datenschutzerklärung
   - AGB

6. **Admin-Funktionen**
   - Angebotsverwaltung
   - Freigabe-Workflow
   - Status-Tracking

7. **Precheck-Export**
   - CSV/Excel Export
   - Für Buchhaltung/Office

### 🟢 Niedrige Priorität

8. **API-Endpoints erweitern**
   - REST API für Mobile Apps
   - Authentication mit JWT

9. **Reporting Dashboard**
   - Analytics
   - KPIs (Conversion Rate, Ø Auftragswert)

10. **Multi-Language Support**
    - Internationalisierung (i18n)
    - Englisch/Deutsch

---

**Status:** 🟢 PRODUKTIONSBEREIT für MVP + Wallbox
**Letztes Update:** 2025-01-08
**Nächster Meilenstein:** n8n-Integration und PDF-Generierung

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)
