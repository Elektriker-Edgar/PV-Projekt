# N8n Workflow Troubleshooting Guide

## 🐛 Fehler: "Cannot read properties of undefined (reading 'precheck_id')"

### Problem
Der "Prepare Data" Node wirft den Fehler, dass `precheck_id` von einem `undefined`-Objekt nicht gelesen werden kann.

### Ursachen

1. **HTTP Request schlägt fehl**
   - URL ist falsch konstruiert
   - Django Server ist nicht erreichbar
   - Endpoint gibt 404/500 zurück

2. **Webhook sendet falsche Daten**
   - `api_base_url` oder `api_endpoints.precheck_data` fehlen
   - Payload-Struktur ist nicht wie erwartet

3. **Django API gibt leere Antwort zurück**
   - Precheck existiert nicht in der Datenbank
   - API-Fehler auf Django-Seite

---

## ✅ Lösung 1: HTTP Request Node richtig konfigurieren

### Wichtige Einstellungen:

```json
{
  "method": "GET",  // ⚠️ Wichtig: GET, nicht POST!
  "url": "={{ $json.body.api_base_url }}{{ $json.body.api_endpoints.precheck_data }}",
  "authentication": "none",
  "options": {
    "timeout": 30000  // 30 Sekunden Timeout
  }
}
```

### Typische Fehler:

❌ **Falsch:** `httpMethod` Parameter verwenden (alte n8n Version)
✅ **Richtig:** `method` Parameter verwenden (n8n v4.2+)

❌ **Falsch:** Kein Timeout gesetzt → Request bricht nach 10s ab
✅ **Richtig:** `timeout: 30000` für längere Anfragen

---

## ✅ Lösung 2: Debug Node einfügen

Füge einen Debug-Node **zwischen** "Get Precheck Data" und "Prepare Data" ein:

```javascript
// DEBUG: Zeigt die Struktur der empfangenen Daten
const inputData = $input.first().json;

console.log('=== DEBUG: Empfangene Daten von HTTP Request ===');
console.log('Typ:', typeof inputData);
console.log('Ist Array?', Array.isArray(inputData));
console.log('Keys:', Object.keys(inputData || {}));
console.log('Erste 500 Zeichen:', JSON.stringify(inputData).substring(0, 500));

// Prüfe ob precheck_id vorhanden ist
if (inputData && inputData.precheck_id) {
  console.log('✅ precheck_id gefunden:', inputData.precheck_id);
  console.log('✅ Kunde:', inputData.customer?.name);
  console.log('✅ PV-Leistung:', inputData.project?.desired_power_kw);
} else {
  console.log('❌ Keine precheck_id in den Daten!');
  console.log('Vollständige Daten:', JSON.stringify(inputData, null, 2));
}

return { json: inputData };
```

### Wo schauen?

1. **n8n Workflow ausführen**
2. **Browser Console öffnen** (F12 → Console)
3. **Debug-Output lesen**

---

## ✅ Lösung 3: Prepare Data Node robuster machen

Ersetze den Code im "Prepare Data" Node mit verbesserter Fehlerbehandlung:

```javascript
// Bereite Daten für OpenAI vor (VERBESSERT)
const inputData = $input.first().json;

// Defensive Checks
if (!inputData) {
  throw new Error('❌ Keine Daten vom HTTP Request empfangen. Prüfe ob der API-Endpoint erreichbar ist.');
}

// Django API gibt direkt ein Objekt zurück (kein Array)
// Die API-Response hat bereits die Struktur: { precheck_id: 123, customer: {...}, site: {...}, ... }
const precheck = inputData;

// Validierung mit detaillierten Fehlermeldungen
if (!precheck.precheck_id) {
  throw new Error(`❌ Ungültige Precheck-Daten - precheck_id fehlt.\n\nEmpfangene Daten:\n${JSON.stringify(inputData, null, 2).substring(0, 500)}`);
}

if (!precheck.customer) {
  console.warn('⚠️ Warnung: Keine Kundendaten vorhanden');
}

if (!precheck.project) {
  console.warn('⚠️ Warnung: Keine Projektdaten vorhanden');
}

// User-Prompt für OpenAI erstellen
const userPrompt = `Bewerte folgende PV-Projekt-Daten:

PRECHECK-ID: ${precheck.precheck_id}

KUNDENDATEN:
${JSON.stringify(precheck.customer, null, 2)}

STANDORTDATEN:
${JSON.stringify(precheck.site, null, 2)}

PROJEKTDATEN:
${JSON.stringify(precheck.project, null, 2)}

PREISDATEN:
${JSON.stringify(precheck.pricing, null, 2)}

VOLLSTÄNDIGKEIT:
${JSON.stringify(precheck.completeness, null, 2)}

---

Erstelle eine strukturierte Bewertung als JSON gemäß Schema.
Besondere Aufmerksamkeit auf:
- customer_notes (Kundenwünsche)
- Kabelstrecken (distance_meter_to_inverter, wallbox_cable_length)
- Hauptsicherung vs. Gesamtleistung

WICHTIG: Antworte NUR mit gültigem JSON, keine Markdown-Code-Blöcke!`;

console.log('✅ Precheck-Daten erfolgreich vorbereitet für OpenAI');
console.log(`   Precheck-ID: ${precheck.precheck_id}`);
console.log(`   Kunde: ${precheck.customer?.name || 'N/A'}`);
console.log(`   PV-Leistung: ${precheck.project?.desired_power_kw || 'N/A'} kW`);

return {
  json: {
    userPrompt: userPrompt,
    precheckData: precheck
  }
};
```

**Was ist neu?**

1. ✅ **Defensive Checks:** Prüft ob `inputData` überhaupt existiert
2. ✅ **Detaillierte Fehlermeldungen:** Zeigt die empfangenen Daten an
3. ✅ **Warnungen:** Gibt Warnings aus, statt zu crashen
4. ✅ **Keine Array-Logik:** Django API gibt direktes Objekt zurück

---

## 🔧 Checkliste für Debugging

### 1. Django Server erreichbar?

```bash
# Test ob Server läuft
curl http://192.168.178.30:8025/api/integrations/precheck/1/
```

**Erwartete Antwort:**
```json
{
  "precheck_id": 1,
  "customer": {...},
  "site": {...},
  "project": {...},
  "pricing": {...}
}
```

### 2. Webhook-Payload korrekt?

Prüfe den Webhook-Aufruf in Django Logs:

```bash
# Django Server Output
INFO:apps.integrations.signals:Sende Webhook an N8n für Precheck 1
INFO:apps.integrations.signals:Webhook erfolgreich an N8n gesendet: Precheck 1
```

### 3. n8n Execution Log prüfen

In n8n:
1. Workflow ausführen
2. Execution anklicken
3. Jeden Node einzeln prüfen
4. HTTP Request → JSON-Output anschauen

### 4. Browser Console öffnen

Während Workflow-Ausführung:
1. `F12` drücken
2. Console-Tab öffnen
3. Debug-Outputs lesen

---

## 📋 Häufige Fehlerquellen

| Symptom | Ursache | Lösung |
|---------|---------|--------|
| `undefined reading 'precheck_id'` | HTTP Request gibt keine Daten zurück | HTTP Request Node Methode auf GET setzen |
| `content.substring is not a function` | OpenAI gibt Objekt statt String zurück | Parse & Validate Node anpassen (siehe unten) |
| `Timeout Error` | Django Server antwortet nicht | Server-URL prüfen, Firewall checken |
| `404 Not Found` | Precheck existiert nicht | Precheck-ID prüfen, DB-Eintrag überprüfen |
| `500 Internal Server Error` | Django API-Fehler | Django Logs checken (`python manage.py runserver`) |
| `Connection refused` | Django Server ist offline | Server starten: `python manage.py runserver` |

---

## ✅ Lösung 4: Parse & Validate für strukturierte JSON-Antworten

### Problem: `content.substring is not a function`

Wenn OpenAI mit `jsonOutput: true` konfiguriert ist, gibt es bereits ein **Objekt** zurück, kein String. Der alte Code versucht aber `.substring()` aufzurufen.

### Symptom:
```
TypeError: content.substring is not a function [line 26]
```

### OpenAI Antwort-Struktur:
```json
{
  "message": {
    "role": "assistant",
    "content": {
      "agent_type": "arbeitsvorbereiter",
      "precheck_id": 59,
      "overall_status": "ok",
      ...
    }
  }
}
```

**Wichtig:** `content` ist bereits ein Objekt, kein String!

### Lösung: Verbesserter Parse & Validate Code

```javascript
// Parse und validiere Agent-Output (VERBESSERT)
const inputData = $input.first().json;

// Content extrahieren
let content;
if (inputData.message && inputData.message.content) {
  content = inputData.message.content;
} else if (inputData.choices && inputData.choices[0]) {
  content = inputData.choices[0].message.content;
} else {
  content = inputData;
}

// Prüfen ob bereits Objekt oder String
let assessment;

if (typeof content === 'object' && content !== null) {
  // ✅ OpenAI mit jsonOutput: true gibt bereits strukturierte Daten zurück
  console.log('✅ Content ist bereits ein Objekt, nutze direkt');
  assessment = content;
} else if (typeof content === 'string') {
  // ⚠️ String muss geparst werden
  console.log('⚠️ Content ist String, parse JSON');
  try {
    // Entferne Markdown-Code-Blöcke falls vorhanden
    const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      assessment = JSON.parse(jsonMatch[1]);
    } else {
      assessment = JSON.parse(content);
    }
  } catch (e) {
    const preview = content.substring(0, 200);
    throw new Error(`❌ JSON Parse Error: ${e.message}.\n\n${preview}`);
  }
} else {
  throw new Error(`❌ Unerwarteter Content-Typ: ${typeof content}`);
}

// Validierung
const required = ['agent_type', 'overall_status', 'recommendations'];
const missing = required.filter(f => !assessment[f]);
if (missing.length > 0) {
  throw new Error(`❌ Fehlende Pflichtfelder: ${missing.join(', ')}`);
}

// Metadaten hinzufügen
assessment.processed_at = new Date().toISOString();
assessment.workflow_execution_id = $execution.id;

const webhookData = $('Webhook').item.json.body;
assessment.webhook_metadata = {
  test_mode: webhookData.test_mode || false,
  customer_email: webhookData.metadata?.customer_email || ''
};

return { json: assessment };
```

**Was ist neu?**

1. ✅ **Type-Check für Content:** Prüft ob Objekt oder String
2. ✅ **Direktes Verwenden bei Objekt:** Kein unnötiges Parsen
3. ✅ **Sicheres String-Parsing:** Nur wenn wirklich String
4. ✅ **Bessere Fehlermeldungen:** Zeigt erwartete vs. vorhandene Felder

---

## 🚀 Schnelltest: Webhook manuell triggern

### Django Dashboard verwenden:

1. Gehe zu: http://192.168.178.30:8025/dashboard/settings/n8n/
2. Webhook-URL eintragen (n8n Webhook-URL)
3. Precheck-ID eingeben (z.B. `1`)
4. "Test Webhook senden" klicken

### Curl verwenden:

```bash
# Webhook manuell an n8n senden
curl -X POST "https://your-n8n-instance.com/webhook/precheck-submitted" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "precheck_submitted",
    "precheck_id": 1,
    "api_base_url": "http://192.168.178.30:8025",
    "api_endpoints": {
      "precheck_data": "/api/integrations/precheck/1/"
    },
    "metadata": {
      "customer_email": "test@example.com",
      "timestamp": "2025-11-22T10:00:00Z"
    }
  }'
```

---

## 📝 Wichtige Django API-Endpunkte

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/integrations/precheck/<id>/` | GET | Precheck-Daten für n8n |
| `/api/integrations/pricing/` | GET | Produktkatalog-Preise |
| `/api/integrations/categories/` | GET | Produktkategorien |
| `/api/integrations/test/webhook/` | POST | Test-Webhook-Empfänger |

---

## 💡 Profi-Tipp: Workflow-Version mit Debug-Node verwenden

Die Datei `N8N_WORKFLOW_ARBEITSVORBEREITER_FIXED.json` enthält:

1. ✅ **Korrigierte HTTP Request Konfiguration** (GET-Methode, Timeout)
2. ✅ **Debug Node** zwischen "Get Precheck Data" und "Prepare Data"
3. ✅ **Verbesserten Prepare Data Node** mit defensiven Checks
4. ✅ **Bessere Fehlerbehandlung** in allen Code-Nodes

**Import:**
1. n8n öffnen
2. Workflows → Import from File
3. `N8N_WORKFLOW_ARBEITSVORBEREITER_FIXED.json` auswählen
4. Credentials konfigurieren (OpenAI API, SMTP)
5. Webhook-URL in Django eintragen

---

## 🆘 Weitere Hilfe

- **Django Logs:** Starte Server mit `python manage.py runserver` und beobachte Output
- **n8n Logs:** Settings → Log Streaming aktivieren
- **Webhook Logs:** Django Dashboard → N8n Integration → Webhook Logs

**Bei weiteren Fragen:** Prüfe die Django Webhook-Logs im Dashboard unter:
http://192.168.178.30:8025/dashboard/settings/n8n/webhook-logs/
