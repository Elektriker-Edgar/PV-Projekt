# n8n Setup-Anleitung für PV-Service

**Ziel:** Automatische Validierung und Angebotserstellung für Precheck-Anfragen

---

## 📋 Voraussetzungen

- n8n installiert und läuft (http://localhost:5678)
- OpenAI API-Key (oder Claude API)
- SMTP-Zugang für E-Mail-Versand
- Django PV-Service läuft (http://192.168.178.30:8025)

---

## 🚀 Schritt 1: n8n Workflow importieren

1. **Datei öffnen:** `E:\ANPR\PV-Service\Docs\N8N_WORKFLOW_EXAMPLE.json`

2. **In n8n importieren:**
   - n8n öffnen: http://localhost:5678
   - Klicke auf **"+ New"** (oben rechts)
   - Klicke auf **"Import from File"**
   - Wähle `N8N_WORKFLOW_EXAMPLE.json`
   - Workflow wird geladen

3. **Webhook-URL kopieren:**
   - Klicke auf den ersten Node "Webhook: Precheck submitted"
   - Kopiere die **Production Webhook URL**
   - Beispiel: `http://localhost:5678/webhook/precheck-submitted`

---

## 🔧 Schritt 2: Webhook-URL in Django konfigurieren

### Option A: Über Dashboard (empfohlen)

1. Django-Dashboard öffnen: http://192.168.178.30:8025/dashboard/settings/n8n/
2. **Webhook URL** eingeben: `http://localhost:5678/webhook/precheck-submitted`
3. **API Key** (optional, später für Production)
4. **Integration aktivieren**: ✅ Checkbox
5. **Speichern** klicken

### Option B: Über .env-Datei

```bash
# E:\ANPR\PV-Service\.env
N8N_WEBHOOK_URL=http://localhost:5678/webhook/precheck-submitted
N8N_API_KEY=
```

Server neu starten:
```bash
python manage.py runserver 192.168.178.30:8025
```

---

## 🔑 Schritt 3: Credentials in n8n konfigurieren

### 3.1 OpenAI API Key

1. n8n → **Credentials** → **Add Credential**
2. Typ: **OpenAI**
3. Name: `openai-credentials`
4. **API Key** eingeben (von https://platform.openai.com/api-keys)
5. **Create** klicken

### 3.2 SMTP für E-Mail-Versand

1. n8n → **Credentials** → **Add Credential**
2. Typ: **SMTP**
3. Name: `smtp-credentials`
4. Konfiguration:
   ```
   Host: smtp.gmail.com (oder dein SMTP-Server)
   Port: 587
   User: deine-email@gmail.com
   Password: dein-app-passwort
   From Email: deine-email@gmail.com
   From Name: EDGARD Elektro Team
   ```
5. **Test Connection** → **Create**

### 3.3 Django API Key (optional, für später)

1. n8n → **Credentials** → **Add Credential**
2. Typ: **HTTP Header Auth**
3. Name: `django-api-key`
4. Header Name: `X-API-Key`
5. Value: `dein-api-key` (später in Django generieren)

---

## 🎯 Schritt 4: Workflow-Nodes konfigurieren

### Node 1: Webhook Trigger
- **Bereits konfiguriert** ✅
- Empfängt POST-Requests von Django

### Node 2: HTTP Request - Precheck-Daten abrufen
- URL: `={{ $json.body.api_base_url + $json.body.api_endpoints.precheck_data }}`
- Method: GET
- **Credential:** Vorerst **None** (AllowAny in Django)
- Später: `django-api-key` für Production

### Node 3: Code - Daten für KI vorbereiten
- **Bereits konfiguriert** ✅
- Extrahiert relevante Daten aus API-Response

### Node 4: OpenAI - Vollständigkeitsprüfung
- Model: `gpt-4o` (oder `gpt-3.5-turbo` für Tests)
- **Credential:** `openai-credentials`
- Temperature: `0.3` (deterministisch)
- Max Tokens: `1500`

**Alternative:** Claude AI verwenden:
- Model: `claude-3-5-sonnet-20241022`
- Credential: Anthropic API Key

### Node 5: Code - KI-Antwort parsen
- **Bereits konfiguriert** ✅
- Extrahiert JSON aus Markdown-Codeblock

### Node 6: IF - Vollständig?
- Bedingung: `{{ $json.status }}` = `VOLLSTÄNDIG`
- **True Branch:** Email an Team (Angebot erstellen)
- **False Branch:** Email an Kunde (Rückfrage)

### Node 7+8: Email Versand
- **Credential:** `smtp-credentials`
- **To (Node 7):** dein-team@example.com
- **To (Node 8):** `{{ $('Code: Daten für KI vorbereiten').item.json.analysis_data.customer.email }}`

### Node 9: Webhook Response
- **Bereits konfiguriert** ✅
- Sendet Bestätigung zurück an Django

---

## ✅ Schritt 5: Workflow aktivieren

1. Workflow speichern: **Ctrl+S**
2. **Activate** Button oben rechts klicken
3. Status sollte auf **Active** wechseln

---

## 🧪 Schritt 6: Test durchführen

### Test 1: Manueller Webhook-Test in Django

1. Öffne Django Dashboard: http://192.168.178.30:8025/dashboard/settings/n8n/
2. Scrolle zu **"Webhook testen"**
3. Gib eine **Precheck-ID** ein (z.B. `66`)
4. Klicke **"Webhook senden"**
5. **Erfolg:** Grüne Meldung mit Response
6. **In n8n prüfen:**
   - Executions → Letzte Ausführung öffnen
   - Jeder Node sollte grün sein ✅

### Test 2: Echter Precheck-Durchlauf

1. Öffne Preisrechner: http://192.168.178.30:8025/precheck/
2. Fülle alle Schritte aus:
   - **Kundendaten:** Name, Email, Telefon
   - **Standort:** Adresse, Gebäudetyp, Hauptsicherung
   - **Fotos:** Mindestens Zählerschrank hochladen
   - **System:** WR-Leistung, Speicher (optional)
   - **Zusammenfassung:** Absenden
3. **Was passiert:**
   - Django speichert Precheck
   - Signal feuert → Webhook an n8n
   - n8n holt Daten via API
   - KI prüft Vollständigkeit
   - E-Mail wird versendet

### Test 3: Verschiedene Szenarien

**Szenario A: Vollständiger Precheck**
- Alle Pflichtfelder ausgefüllt
- Fotos hochgeladen
- Technisch plausibel
- **Erwartung:** E-Mail an Team "Angebot erstellen"

**Szenario B: Unvollständiger Precheck**
- Keine Fotos hochgeladen
- Fehlende Montageorte
- **Erwartung:** E-Mail an Kunde "Rückfrage"

**Szenario C: Technisch problematisch**
- 20kW WR bei 35A Hauptsicherung
- **Erwartung:** KI erkennt Plausibilitätsproblem

---

## 📊 Schritt 7: Monitoring & Logs

### In n8n:
- **Executions** Tab öffnen
- Letzte Workflow-Ausführungen sehen
- Bei Fehlern: Node anklicken → Error-Details

### In Django:
- **Admin:** http://192.168.178.30:8025/admin/integrations/webhooklog/
- Alle Webhook-Calls mit Payload & Response
- **Dashboard:** http://192.168.178.30:8025/dashboard/settings/n8n/webhook-logs/
- Übersichtliche Darstellung mit Filtern

---

## 🔒 Schritt 8: Production-Konfiguration (später)

### 8.1 API-Key-Authentifizierung aktivieren

**In Django:**
```python
# apps/integrations/api_views.py
@authentication_classes([N8nAPIKeyAuthentication])
@permission_classes([IsAuthenticated])
def get_precheck_data(request, precheck_id):
    ...
```

**In n8n:**
- HTTP Request Node → Credential: `django-api-key`
- Header: `X-API-Key: dein-geheimer-key`

### 8.2 Webhook-URL auf Production-Server

```bash
# .env
N8N_WEBHOOK_URL=https://n8n.deine-domain.de/webhook/precheck-submitted
BASE_URL=https://pv-service.deine-domain.de
```

### 8.3 Rate Limiting & Retry-Logik

**In Django:**
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
    }
}
```

**In n8n:**
- HTTP Request Node → Retry on Fail: `3 Mal`
- Wait Between Tries: `5 Sekunden`

---

## 🎓 Workflow-Logik (Übersicht)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. WEBHOOK TRIGGER                                          │
│    Django sendet: { precheck_id, api_endpoints }           │
├─────────────────────────────────────────────────────────────┤
│ 2. HTTP REQUEST                                             │
│    GET /api/integrations/precheck/{id}/                    │
│    → Vollständige Kundendaten, Fotos, Pricing              │
├─────────────────────────────────────────────────────────────┤
│ 3. CODE NODE                                                │
│    Daten strukturieren für KI-Analyse                      │
├─────────────────────────────────────────────────────────────┤
│ 4. OPENAI NODE                                              │
│    Prompt: "Prüfe Vollständigkeit dieser PV-Anfrage..."    │
│    Response: {                                              │
│      completeness_score: 85,                                │
│      status: "VOLLSTÄNDIG",                                 │
│      missing_data: [],                                      │
│      recommendation: "..."                                  │
│    }                                                        │
├─────────────────────────────────────────────────────────────┤
│ 5. CODE NODE                                                │
│    Parse JSON aus KI-Antwort                               │
├─────────────────────────────────────────────────────────────┤
│ 6. IF NODE: status == "VOLLSTÄNDIG"?                       │
│    ├─ TRUE  → Email an Team (Angebot erstellen)           │
│    └─ FALSE → Email an Kunde (Rückfrage)                  │
├─────────────────────────────────────────────────────────────┤
│ 7. WEBHOOK RESPONSE                                         │
│    Bestätigung zurück an Django                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Problem: "Webhook konnte nicht erreicht werden"

**Lösung:**
1. n8n läuft? → `http://localhost:5678` öffnen
2. Workflow aktiviert? → Grüner "Active" Status
3. Webhook-URL korrekt in Django? → Dashboard prüfen
4. Firewall-Regel? → Localhost sollte immer erreichbar sein

### Problem: "API-Endpoint gibt 500 Error"

**Lösung:**
1. Django-Logs prüfen: Server-Console
2. Precheck-ID existiert? → Django Admin prüfen
3. Site & Customer vorhanden? → API benötigt beide

### Problem: "KI-Antwort kann nicht geparst werden"

**Lösung:**
1. OpenAI API-Key gültig? → n8n Credentials prüfen
2. Model-Name korrekt? → `gpt-4o` oder `gpt-3.5-turbo`
3. Response Format prüfen → n8n Execution Output ansehen

### Problem: "E-Mail wird nicht versendet"

**Lösung:**
1. SMTP-Credentials korrekt? → Test Connection in n8n
2. Gmail: App-Passwort verwenden (nicht normales Passwort)
3. E-Mail-Adresse im `To:` Feld korrekt?

---

## 📈 Erweiterungen (Optional)

### 1. PDF-Angebot automatisch erstellen

**Neuer Node nach "Email: Angebot erstellen":**
```
HTTP Request: POST /api/quotes/create-from-precheck/
Body: { "precheck_id": {{ $json.precheck_id }} }
```

### 2. Slack-Benachrichtigung statt E-Mail

**Slack Node hinzufügen:**
```
Channel: #pv-anfragen
Message: "Neue PV-Anfrage von {{ $json.customer.name }}"
```

### 3. Google Sheets Logging

**Google Sheets Node:**
- Jede Anfrage in Tabelle loggen
- Spalten: Datum, Kunde, Leistung, Status, Preis

### 4. Zweite KI-Prüfung für technische Details

**Zusätzlicher OpenAI Node:**
- Prompt: "Bewerte die technische Machbarkeit..."
- Prüft: WR vs. Sicherung, Speicher-Größe, Wallbox-Last

---

## 📚 Weiterführende Dokumentation

- **API-Dokumentation:** `E:\ANPR\PV-Service\Docs\CLAUDE_API.md`
- **N8n Integration Plan:** `E:\ANPR\PV-Service\Docs\N8N_INTEGRATION_PLAN.md`
- **Workflow JSON:** `E:\ANPR\PV-Service\Docs\N8N_WORKFLOW_EXAMPLE.json`

---

**Erstellt:** 2025-11-20
**Status:** ✅ Bereit für Implementierung
**Nächstes Update:** Nach erstem Production-Einsatz
