# 🔧 Parse & Validate - FINAL FIX

## Problem: `Invalid expression [line 67]`

Der Code versucht auf den Webhook-Node zuzugreifen:
```javascript
const webhookData = $('Webhook').item.json.body;  // ❌ Crash wenn nicht verbunden
```

---

## ✅ FINALER CODE (Copy-Paste Ready)

Ersetze den **kompletten Code** im "Parse & Validate" Node mit:

```javascript
// Parse und validiere Agent-Output (FINAL VERSION)
const inputData = $input.first().json;

console.log('=== DEBUG: Parse & Validate Input ===');
console.log('Input Type:', typeof inputData);
console.log('Input Keys:', Object.keys(inputData || {}));

// Verschiedene Antwort-Formate unterstützen
let content;
if (inputData.message && inputData.message.content) {
  content = inputData.message.content;
} else if (inputData.choices && inputData.choices[0]) {
  content = inputData.choices[0].message.content;
} else if (typeof inputData === 'string') {
  content = inputData;
} else {
  content = inputData;
}

console.log('Content Type:', typeof content);
console.log('Content ist Objekt?', typeof content === 'object' && content !== null);

// Parse JSON (oder verwende direkt falls bereits Objekt)
let assessment;

if (typeof content === 'object' && content !== null) {
  // OpenAI mit jsonOutput: true gibt bereits strukturierte Daten zurück
  console.log('✅ Content ist bereits ein Objekt, nutze direkt');
  assessment = content;
} else if (typeof content === 'string') {
  // String muss geparst werden
  console.log('⚠️ Content ist String, parse JSON');
  try {
    // Entferne Markdown-Code-Blöcke falls vorhanden
    const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      console.log('Markdown-Code-Block gefunden, extrahiere JSON');
      assessment = JSON.parse(jsonMatch[1]);
    } else {
      assessment = JSON.parse(content);
    }
  } catch (e) {
    const preview = typeof content === 'string' ? content.substring(0, 200) : JSON.stringify(content).substring(0, 200);
    throw new Error(`❌ JSON Parse Error: ${e.message}.\n\nErste 200 Zeichen:\n${preview}`);
  }
} else {
  throw new Error(`❌ Unerwarteter Content-Typ: ${typeof content}`);
}

console.log('Assessment Keys:', Object.keys(assessment || {}));
console.log('Assessment precheck_id:', assessment.precheck_id);

// Validierung
const required = ['agent_type', 'overall_status', 'recommendations'];
const missing = required.filter(f => !assessment[f]);
if (missing.length > 0) {
  throw new Error(`❌ Fehlende Pflichtfelder: ${missing.join(', ')}\n\nVorhandene Felder: ${Object.keys(assessment).join(', ')}`);
}

console.log('✅ Validierung erfolgreich');

// Metadaten hinzufügen
assessment.processed_at = new Date().toISOString();
assessment.workflow_execution_id = $execution.id;

// Original Webhook-Daten (DEFENSIV - prüfe ob Webhook-Node existiert)
let webhookData = {};
try {
  // Versuche Webhook-Daten zu holen
  const webhookNode = $('Webhook');
  if (webhookNode && webhookNode.item && webhookNode.item.json) {
    webhookData = webhookNode.item.json.body || webhookNode.item.json;
  }
} catch (e) {
  // Webhook-Node nicht erreichbar - verwende leeres Objekt
  console.warn('⚠️ Webhook-Node nicht erreichbar, verwende Default-Werte');
}

assessment.webhook_metadata = {
  test_mode: webhookData.test_mode || false,
  customer_email: webhookData.metadata?.customer_email || ''
};

console.log('✅ Parse & Validate abgeschlossen');
console.log(`   Precheck-ID: ${assessment.precheck_id}`);
console.log(`   Status: ${assessment.overall_status}`);
console.log(`   Empfehlungen: ${assessment.recommendations?.length || 0}`);

return { json: assessment };
```

---

## 🎯 Was wurde geändert?

### 1. Sicherer Webhook-Zugriff (Zeile 67+)

**ALT (crasht):**
```javascript
const webhookData = $('Webhook').item.json.body;  // ❌ Crash
```

**NEU (sicher):**
```javascript
let webhookData = {};
try {
  const webhookNode = $('Webhook');
  if (webhookNode && webhookNode.item && webhookNode.item.json) {
    webhookData = webhookNode.item.json.body || webhookNode.item.json;
  }
} catch (e) {
  console.warn('⚠️ Webhook-Node nicht erreichbar, verwende Default-Werte');
}
```

### 2. Sicherer String-Zugriff

**ALT:**
```javascript
const preview = content.substring(0, 200);  // ❌ Crash wenn content kein String
```

**NEU:**
```javascript
const preview = typeof content === 'string'
  ? content.substring(0, 200)
  : JSON.stringify(content).substring(0, 200);
```

### 3. Safe Access für Arrays

```javascript
console.log(`Empfehlungen: ${assessment.recommendations?.length || 0}`);
```

---

## 🚀 Installation

### Schritt 1: n8n Node öffnen
1. n8n Workflow öffnen
2. **"Parse & Validate"** Node anklicken
3. **Edit Code** klicken

### Schritt 2: Code ersetzen
1. **Alles markieren** (Ctrl+A)
2. **Löschen** (Delete)
3. **Neuen Code einfügen** (Ctrl+V)
4. **Save** klicken

### Schritt 3: Testen
1. Workflow ausführen
2. Browser Console öffnen (F12)
3. Debug-Output prüfen

---

## 📊 Erwarteter Debug-Output

```
=== DEBUG: Parse & Validate Input ===
Input Type: object
Input Keys: index, message, finish_reason

Content Type: object
Content ist Objekt? true
✅ Content ist bereits ein Objekt, nutze direkt

Assessment Keys: agent_type, precheck_id, overall_status, ...
Assessment precheck_id: 59

✅ Validierung erfolgreich

✅ Parse & Validate abgeschlossen
   Precheck-ID: 59
   Status: ok
   Empfehlungen: 7
```

---

## 🔍 Warum crashte der alte Code?

### Problem 1: Webhook-Node nicht verbunden
```javascript
$('Webhook').item.json.body
```

n8n wirft `Invalid expression` wenn:
- Der Node "Webhook" nicht existiert
- Der Node nicht im Ausführungspfad liegt
- Keine Verbindung zum Parse & Validate Node besteht

### Problem 2: content.substring auf Objekt
```javascript
content.substring(0, 200)  // ❌ Crash wenn content ein Objekt ist
```

### Lösung: Try-Catch + Type-Checks
```javascript
try {
  const webhookNode = $('Webhook');
  // ...
} catch (e) {
  console.warn('Webhook nicht erreichbar');
}
```

---

## 💡 Alternative: Webhook-Metadata entfernen

Falls du die Webhook-Metadata nicht brauchst, kannst du diese Zeilen auch komplett entfernen:

```javascript
// Metadaten hinzufügen
assessment.processed_at = new Date().toISOString();
assessment.workflow_execution_id = $execution.id;

// ❌ Diese Zeilen kannst du löschen:
// assessment.webhook_metadata = { ... };

return { json: assessment };
```

Dann ist `webhook_metadata` einfach nicht im Output.

---

## 🆘 Weitere Troubleshooting

### Fehler bleibt bestehen?

**Option 1: Workflow-Verbindungen prüfen**
1. Stelle sicher, dass **alle Nodes verbunden** sind
2. Webhook → Get Precheck Data → DEBUG → Prepare Data → OpenAI → **Parse & Validate**

**Option 2: Kompletten FIXED Workflow nutzen**
1. Importiere `N8N_WORKFLOW_ARBEITSVORBEREITER_FIXED.json`
2. Alle Fixes sind bereits enthalten
3. Workflow ist getestet

---

## ✅ Checkliste

- [ ] Code im Parse & Validate Node komplett ersetzt
- [ ] Workflow gespeichert
- [ ] Workflow ausgeführt
- [ ] Browser Console (F12) geöffnet
- [ ] Debug-Output gelesen
- [ ] Kein Fehler mehr

---

**Bei weiteren Problemen:**
- Prüfe Browser Console (F12)
- Prüfe n8n Execution Log
- Stelle sicher alle Nodes sind verbunden
- Nutze den FIXED Workflow als Referenz
