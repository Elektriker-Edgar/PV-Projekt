# N8n Workflow Installation: Arbeitsvorbereiter Agent

## 📋 Übersicht

Diese Anleitung führt Sie Schritt-für-Schritt durch die Installation und Konfiguration des Arbeitsvorbereiter-Agent Workflows in n8n.

**Workflow-Datei:** `docs/N8N_WORKFLOW_ARBEITSVORBEREITER.json`

---

## 🎯 Workflow-Funktionen

### Was macht der Workflow?

1. **Empfängt Webhook** von Django wenn Precheck eingereicht wird
2. **Holt Precheck-Daten** von Django API
3. **KI-Bewertung** durch OpenAI GPT-4 (Arbeitsvorbereiter-Agent)
4. **Parst & Validiert** das JSON-Ergebnis
5. **Verzweigt nach Status:**
   - ✅ **OK** → E-Mail an Team (Angebot erstellen)
   - ⚠️ **Review** → E-Mail an Sales (Rückfragen nötig)
   - 🔴 **Not Feasible** → E-Mail an Management (Ablehnung)
6. **Sendet Response** zurück an Django
7. **Speichert Output** für nachfolgende Workflows

### Workflow-Nodes (11 Nodes)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Webhook Trigger (Precheck Submitted)                   │
│     ↓                                                        │
│  2. HTTP Request (Get Precheck Data from Django)           │
│     ↓                                                        │
│  3. OpenAI (Arbeitsvorbereiter Agent - GPT-4)              │
│     ↓                                                        │
│  4. Code (Parse & Validate JSON)                           │
│     ↓                        ↓                              │
│  5. Switch (Status)      10. Set Variables (für Quote Agent)│
│     ├─ OK ──────────→ 6. Code (Email OK)                   │
│     ├─ Review ───────→ 7. Code (Email Review)              │
│     └─ Not Feasible ─→ 8. Code (Email Not Feasible)        │
│                           ↓                                  │
│                        9. Send Email                        │
│                           ↓                                  │
│                       11. Webhook Response                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Voraussetzungen

### 1. n8n Installation
- n8n >= 1.0.0 installiert und lauffähig
- Zugriff auf n8n UI (z.B. `http://localhost:5678`)

### 2. Erforderliche Credentials

#### A) OpenAI API
- OpenAI Account mit API-Key
- Guthaben für GPT-4 vorhanden
- **Kosten:** ca. $0.03-0.05 pro Bewertung

#### B) SMTP E-Mail Account
- SMTP Server (z.B. Gmail, Outlook, eigener Server)
- Zugangsdaten (Host, Port, User, Password)

#### C) Django API (Optional: HTTP Header Auth)
- Django Backend läuft und ist erreichbar
- API-Key für Authentifizierung (falls aktiviert)

---

## 📥 Installation

### Schritt 1: Workflow importieren

1. **n8n öffnen:** `http://localhost:5678`
2. **Neuer Workflow:** Klick auf "Add Workflow" (+ Button)
3. **Import öffnen:**
   - Menü (3 Punkte oben rechts) → "Import from File"
   - ODER: Strg+O / Cmd+O
4. **Datei auswählen:**
   - Navigate zu: `E:\ANPR\PV-Service\docs\N8N_WORKFLOW_ARBEITSVORBEREITER.json`
   - Klick "Open"
5. **Import bestätigen:** Workflow sollte jetzt mit allen 11 Nodes sichtbar sein

**Erwartetes Ergebnis:**
```
✅ Workflow "PV-Service: Arbeitsvorbereiter Agent" importiert
✅ 11 Nodes sichtbar
⚠️ Rote Ausrufezeichen bei Nodes mit fehlenden Credentials
```

---

### Schritt 2: Credentials konfigurieren

#### A) OpenAI API Credential

1. **Node öffnen:** Klick auf "OpenAI: Arbeitsvorbereiter Agent"
2. **Credential erstellen:**
   - Bei "Credential to connect with" → "Create New"
   - Name: `OpenAI API` (oder beliebig)
3. **API Key eingeben:**
   - API Key: `sk-...` (von OpenAI Dashboard)
   - Optional: Organization ID
4. **Speichern:** Klick "Create"

**OpenAI API Key erhalten:**
```
1. Gehe zu: https://platform.openai.com/api-keys
2. Klick "Create new secret key"
3. Name: "n8n PV-Service"
4. Kopiere den Key (sk-...)
5. WICHTIG: Key sicher speichern (wird nur einmal angezeigt!)
```

#### B) SMTP E-Mail Credential

1. **Node öffnen:** Klick auf "Send Email: Notification"
2. **Credential erstellen:**
   - Bei "Credential to connect with" → "Create New"
   - Name: `SMTP Account` (oder beliebig)
3. **SMTP Settings:**
   ```
   Host: smtp.gmail.com (Beispiel Gmail)
   Port: 587
   User: your-email@gmail.com
   Password: ******** (App-Password bei Gmail!)

   Security: TLS
   ```
4. **Speichern:** Klick "Create"

**Gmail App-Password erstellen:**
```
1. Google Account → Sicherheit → 2-Faktor-Authentifizierung
2. App-Passwörter → "Mail" → "Sonstiges" (n8n)
3. Generiertes Passwort kopieren (16 Zeichen)
4. Dieses Passwort in n8n verwenden (NICHT Ihr normales Gmail-Passwort!)
```

**Alternative SMTP Provider:**
```
Outlook/Hotmail:
  Host: smtp.office365.com
  Port: 587

Eigener Server:
  Host: mail.ihre-domain.de
  Port: 587 oder 465
  Security: TLS oder SSL
```

#### C) HTTP Header Auth (Optional)

Falls Ihre Django API einen API-Key benötigt:

1. **Node öffnen:** "HTTP Request: Get Precheck Data"
2. **Authentication:** "Predefined Credential Type" → "Header Auth"
3. **Credential erstellen:**
   - Name: `Django API Key`
   - Header Name: `X-API-Key`
   - Header Value: `ihr-django-api-key`
4. **Speichern**

**Hinweis:** Der API-Key wird auch vom Webhook übergeben (`x-api-key` Header), daher ist diese Credential optional.

---

### Schritt 3: Webhook konfigurieren

1. **Node öffnen:** "Webhook: Precheck Submitted"
2. **Test Webhook URL kopieren:**
   - Klick auf "Test URL" (Kopier-Icon)
   - URL sieht aus wie: `http://localhost:5678/webhook-test/precheck-submitted`
3. **Production Webhook URL:**
   - Nach Aktivierung des Workflows: `http://localhost:5678/webhook/precheck-submitted`

**Django Webhook konfigurieren:**

In `apps/quotes/api_views.py` (oder wo auch immer der Webhook gesendet wird):

```python
import requests

# In der send_n8n_webhook Funktion:
def send_n8n_webhook(precheck_id, test_mode=False):
    webhook_url = "http://localhost:5678/webhook/precheck-submitted"
    # Für Tests: http://localhost:5678/webhook-test/precheck-submitted

    payload = {
        "event": "precheck_submitted",
        "precheck_id": precheck_id,
        "test_mode": test_mode,
        "api_base_url": "http://192.168.178.30:8025",
        "api_endpoints": {
            "precheck_data": f"/api/integrations/precheck/{precheck_id}/",
            "pricing_data": "/api/integrations/pricing/"
        },
        "metadata": {
            "customer_email": precheck.customer.email,
            "has_customer": True,
            "has_site": True,
            "timestamp": timezone.now().isoformat()
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": settings.N8N_API_KEY  # Optional
    }

    response = requests.post(webhook_url, json=payload, headers=headers)
    return response
```

---

### Schritt 4: E-Mail-Adressen anpassen

**Wichtig:** Passen Sie die E-Mail-Adressen an Ihr Team an!

#### Node: "Code: Email OK Status"
```javascript
// Zeile 89-90:
return {
  json: {
    to: 'team@edgard-elektro.de',  // ← ÄNDERN SIE DIESE E-MAIL!
    subject: `✅ Neue PV-Anfrage #${assessment.precheck_id} - Angebot erstellen`,
    ...
  }
};
```

#### Node: "Code: Email Review Status"
```javascript
// Zeile ändern:
to: 'sales@edgard-elektro.de',  // ← ÄNDERN SIE DIESE E-MAIL!
```

#### Node: "Code: Email Not Feasible"
```javascript
// Zeilen ändern:
to: 'management@edgard-elektro.de',  // ← ÄNDERN!
cc: 'sales@edgard-elektro.de',       // ← ÄNDERN!
```

#### Node: "Send Email: Notification"
```javascript
// FROM-Adresse anpassen:
fromEmail: "noreply@edgard-elektro.de"  // ← ÄNDERN SIE DIESE E-MAIL!
```

---

### Schritt 5: API Base URL anpassen (falls nötig)

Falls Ihr Django Server NICHT auf `http://192.168.178.30:8025` läuft:

**Option A: In Django Webhook ändern**
```python
# apps/quotes/api_views.py
"api_base_url": "http://IHRE-IP:PORT",  # ← Anpassen
```

**Option B: In n8n Node ändern**
```javascript
// Node "HTTP Request: Get Precheck Data"
// URL wird automatisch aus Webhook gebaut:
url: "={{ $json.body.api_base_url }}{{ $json.body.api_endpoints.precheck_data }}"
// → Keine Änderung nötig, wenn Django korrekt sendet
```

---

## 🧪 Testen

### Test 1: Workflow aktivieren

1. **Workflow speichern:** Strg+S / Cmd+S
2. **Workflow aktivieren:** Toggle oben rechts auf "Active"
3. **Status prüfen:** "Active" sollte grün leuchten

**Erwartetes Ergebnis:**
```
✅ Workflow aktiv
✅ Webhook lauscht auf: http://localhost:5678/webhook/precheck-submitted
```

---

### Test 2: Manueller Test mit Test-Daten

1. **Webhook Test-Mode:**
   - Klick auf "Webhook: Precheck Submitted"
   - Klick "Listen for Test Event"
   - Node wartet jetzt auf Test-Daten

2. **Test-Request senden (via Postman/cURL):**

```bash
curl -X POST http://localhost:5678/webhook-test/precheck-submitted \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-123" \
  -d '{
    "event": "precheck_submitted",
    "precheck_id": 64,
    "test_mode": true,
    "api_base_url": "http://192.168.178.30:8025",
    "api_endpoints": {
      "precheck_data": "/api/integrations/precheck/64/",
      "pricing_data": "/api/integrations/pricing/"
    },
    "metadata": {
      "customer_email": "max.mustermann.test@example.com",
      "has_customer": true,
      "has_site": true,
      "timestamp": "2025-11-21T12:00:00Z"
    }
  }'
```

3. **Workflow Execution beobachten:**
   - Nodes sollten nacheinander grün werden
   - Bei Fehlern: Rote Node → Klick auf Node → "Error" Tab anschauen

**Erwartete Ausführungszeit:** 10-20 Sekunden

---

### Test 3: Production Test (von Django)

1. **Django Precheck einreichen:**
   - Öffne: `http://192.168.178.30:8025/precheck/`
   - Fülle Formular aus und submit

2. **n8n Executions prüfen:**
   - n8n → Menü → "Executions"
   - Neueste Execution sollte erscheinen
   - Status: "Success" (grün)

3. **E-Mail prüfen:**
   - Inbox der konfigurierten E-Mail-Adresse checken
   - E-Mail sollte angekommen sein mit Bewertung

**Mögliche Stati:**
```
✅ Success (grün)    → Alles OK, E-Mail versendet
⚠️ Warning (gelb)   → Teilweise erfolgreich
❌ Error (rot)      → Fehler aufgetreten (siehe Logs)
```

---

## 🐛 Troubleshooting

### Problem 1: "OpenAI Authentication Failed"

**Symptom:**
```
Error: Invalid API Key
```

**Lösung:**
1. OpenAI API Key prüfen (Gültigkeit auf platform.openai.com)
2. Key in n8n Credential neu eingeben
3. Sicherstellen, dass Guthaben vorhanden ist

---

### Problem 2: "Cannot reach Django API"

**Symptom:**
```
Error: ECONNREFUSED 192.168.178.30:8025
```

**Lösung:**
1. Django Server läuft? (`python manage.py runserver`)
2. IP-Adresse korrekt? (Check mit `ipconfig` / `ifconfig`)
3. Firewall blockiert Port 8025?
4. Von n8n Server aus erreichbar? (`curl http://192.168.178.30:8025/api/integrations/precheck/1/`)

**Alternative:** Django API über öffentliche Domain erreichbar machen:
```python
# settings.py
ALLOWED_HOSTS = ['*']  # Nur für Tests!
```

---

### Problem 3: "Email Send Failed"

**Symptom:**
```
Error: Invalid login: 535 Authentication failed
```

**Lösung Gmail:**
1. 2-Faktor-Authentifizierung aktiviert?
2. App-Passwort generiert (NICHT normales Passwort)?
3. "Weniger sichere Apps" deaktiviert → App-Passwort verwenden

**Lösung Outlook:**
```
Host: smtp.office365.com
Port: 587
Security: STARTTLS
```

**Test SMTP direkt:**
```bash
# Mit telnet testen
telnet smtp.gmail.com 587
EHLO localhost
STARTTLS
AUTH LOGIN
# ... (Base64 encoded credentials)
```

---

### Problem 4: "Parse Error - Invalid JSON"

**Symptom:**
```
Error: Parse-Fehler: Unexpected token < in JSON
```

**Ursache:** OpenAI hat Text statt JSON zurückgegeben

**Lösung:**
1. **System Prompt prüfen:** Enthält "Antworte NUR mit gültigem JSON"?
2. **Response Format:** Bei OpenAI Node → Options → Response Format: `json_object`
3. **Temperature reduzieren:** 0.3 → 0.1 (präziser)
4. **User Prompt ergänzen:**
   ```
   WICHTIG: Antworte NUR mit gültigem JSON, keine Markdown-Code-Blöcke!
   Beginne direkt mit { und ende mit }
   ```

**Notfall-Fix im Code Node:**
```javascript
// In "Code: Parse & Validate" (Zeile 13-18)
const jsonMatch = assessment.match(/```json\s*([\s\S]*?)\s*```/);
if (jsonMatch) {
  assessmentData = JSON.parse(jsonMatch[1]);  // Entfernt Markdown
} else {
  assessmentData = JSON.parse(assessment.trim());
}
```

---

### Problem 5: "Workflow triggt nicht automatisch"

**Symptom:**
- Django sendet Webhook, aber n8n reagiert nicht

**Lösung:**
1. **Workflow aktiv?** Toggle oben rechts muss grün sein
2. **Richtige URL?**
   - Production: `/webhook/precheck-submitted`
   - NICHT: `/webhook-test/precheck-submitted`
3. **n8n Logs checken:**
   ```bash
   # Docker
   docker logs n8n

   # NPM
   ~/.n8n/logs/
   ```
4. **Webhook Endpoint testen:**
   ```bash
   curl -X POST http://localhost:5678/webhook/precheck-submitted \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'

   # Sollte nicht 404 returnen!
   ```

---

## 🔐 Sicherheit

### Production Best Practices

#### 1. API-Keys schützen
```
❌ NICHT: API-Keys im Code hardcoden
✅ DO: Environment Variables verwenden
```

**n8n Environment Variables:**
```bash
# .env (im n8n Verzeichnis)
N8N_ENCRYPTION_KEY=your-encryption-key
DJANGO_API_KEY=your-django-api-key
OPENAI_API_KEY=sk-...

# In Workflow verwenden:
{{ $env.DJANGO_API_KEY }}
```

#### 2. Webhook absichern

**Django sendet X-API-Key:**
```python
# Django webhook
headers = {
    "X-API-Key": settings.N8N_WEBHOOK_SECRET
}
```

**n8n validiert:**
```javascript
// In "Code: Parse & Validate" einfügen:
const webhookData = $('Webhook: Precheck Submitted').item.json.body;
const apiKey = $('Webhook: Precheck Submitted').item.json.headers['x-api-key'];

const expectedKey = $env.N8N_WEBHOOK_SECRET;
if (apiKey !== expectedKey) {
  throw new Error('Invalid API Key - Unauthorized');
}
```

#### 3. HTTPS verwenden (Production)

**n8n mit HTTPS:**
```bash
# docker-compose.yml
environment:
  - N8N_PROTOCOL=https
  - N8N_HOST=n8n.ihre-domain.de
  - N8N_PORT=443
  - WEBHOOK_URL=https://n8n.ihre-domain.de/
```

**Django Webhook auf HTTPS:**
```python
webhook_url = "https://n8n.ihre-domain.de/webhook/precheck-submitted"
```

#### 4. Rate Limiting

**n8n Workflow Settings:**
```
Settings → Max Execution Time: 300 (5 Minuten)
Settings → Timezone: Europe/Berlin
```

---

## 📊 Monitoring & Logs

### Executions überwachen

**n8n UI:**
1. Menü → "Executions"
2. Filter nach:
   - Status (Success / Error / Warning)
   - Workflow: "PV-Service: Arbeitsvorbereiter Agent"
   - Zeitraum

**Wichtige Metriken:**
```
✅ Success Rate: > 95%
⏱️ Avg. Execution Time: 10-20 Sekunden
💰 OpenAI Costs: ~$0.03-0.05 pro Execution
```

### Error Notifications

**n8n Error Workflow:**
```json
Settings → Error Workflow → "Create New"
```

**Simple Error Notification:**
```
IF: Error in "Arbeitsvorbereiter Agent"
THEN: Send Email to admin@edgard-elektro.de
```

---

## 💰 Kosten-Kalkulation

### OpenAI Kosten

**GPT-4 Turbo Pricing (Stand 2024):**
```
Input:  $0.01 / 1K tokens
Output: $0.03 / 1K tokens

Durchschnitt pro Bewertung:
- Input:  ~2.000 tokens = $0.02
- Output: ~1.500 tokens = $0.045
────────────────────────────────
TOTAL: ~$0.065 pro Bewertung
```

**Alternative: GPT-4o-mini (günstiger, etwas weniger präzise):**
```
Input:  $0.00015 / 1K tokens
Output: $0.0006 / 1K tokens
────────────────────────────────
TOTAL: ~$0.001 pro Bewertung (99% günstiger!)
```

**Empfehlung:**
- **Development:** GPT-4o-mini
- **Production:** GPT-4 Turbo

**Kosten-Hochrechnung (100 Prechecks/Monat):**
```
GPT-4 Turbo: 100 × $0.065 = $6.50 / Monat
GPT-4o-mini:  100 × $0.001 = $0.10 / Monat
```

---

## 🚀 Production Deployment

### Checkliste vor Go-Live

- [ ] **Credentials:**
  - [ ] OpenAI API Key mit Guthaben
  - [ ] SMTP Account funktioniert
  - [ ] Django API erreichbar

- [ ] **E-Mail-Adressen:**
  - [ ] Alle Platzhalter ersetzt (team@, sales@, management@)
  - [ ] Test-E-Mail erfolgreich empfangen

- [ ] **Webhook:**
  - [ ] Django sendet an Production URL (nicht Test-URL)
  - [ ] API-Key Validierung implementiert (optional)

- [ ] **Security:**
  - [ ] HTTPS für n8n (falls öffentlich)
  - [ ] Environment Variables für Secrets
  - [ ] Webhook Secret validiert

- [ ] **Monitoring:**
  - [ ] Error Workflow konfiguriert
  - [ ] Admin-Benachrichtigungen bei Fehlern

- [ ] **Testing:**
  - [ ] 3 Test-Cases durchgeführt (OK, Review, Not Feasible)
  - [ ] E-Mails kommen korrekt an
  - [ ] Response an Django funktioniert

---

## 🔄 Workflow Updates

### Wie aktualisiere ich den Workflow?

**Option 1: Manuell Nodes ändern**
1. Workflow in n8n öffnen
2. Node doppelklicken → Änderungen vornehmen
3. Save

**Option 2: Neuen Workflow importieren**
1. Alten Workflow deaktivieren
2. Export des aktuellen Workflows (Backup!)
3. Neuen Workflow importieren
4. Credentials neu verknüpfen
5. Testen
6. Aktivieren

**Wichtig:** Bei jedem Update Credentials neu verknüpfen!

---

## 📚 Nächste Schritte

### Nach erfolgreicher Installation:

1. **Quote Agent Workflow** (geplant)
   - Input: Arbeitsvorbereiter-Output (aus Set Variables Node)
   - Output: Angebot als PDF

2. **Correspondence Agent Workflow** (geplant)
   - Input: Arbeitsvorbereiter + Quote
   - Output: E-Mail an Kunde

3. **Dashboard Integration** (geplant)
   - Agent-Bewertungen in Django anzeigen
   - Status-Tracking

---

## 📞 Support

### Bei Problemen:

1. **n8n Community Forum:** https://community.n8n.io/
2. **OpenAI Support:** https://help.openai.com/
3. **Projekt-Dokumentation:** `docs/CLAUDE.md`

### Logs & Debugging:

```bash
# n8n Logs (Docker)
docker logs -f n8n

# n8n Logs (NPM)
tail -f ~/.n8n/logs/n8n.log

# Django Logs
tail -f logs/django.log
```

---

**Installation abgeschlossen!** 🎉

Der Arbeitsvorbereiter-Agent Workflow ist jetzt einsatzbereit.

**Dokumentiert von:** Claude Code (Anthropic)
**Datum:** 2025-11-21
**Version:** 1.0
**Status:** ✅ Produktionsbereit
