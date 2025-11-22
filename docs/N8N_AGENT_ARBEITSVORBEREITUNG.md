# N8n KI-Agent: Arbeitsvorbereiter Elektroinstallation

## 📋 Übersicht

**Agent-Typ:** Arbeitsvorbereiter / Technischer Prüfer
**Spezialisierung:** Elektroinstallation PV-Anlagen
**Position im Workflow:** Erster Agent nach Daten-Abruf
**Input:** Vollständige Precheck-Daten von Django API
**Output:** Strukturierte JSON-Bewertung für nachfolgende Agenten

---

## 🎯 Aufgaben des Agenten

### 1. Plausibilitätsprüfung
- ✅ PV-Leistung passend zur Gebäudegröße
- ✅ Speichergröße im Verhältnis zur PV-Leistung
- ✅ Hauptsicherung ausreichend dimensioniert
- ✅ Kabelstrecken realistisch
- ✅ Wallbox-Anforderungen erfüllbar

### 2. Vollständigkeitsprüfung
- ✅ Alle erforderlichen Kundendaten vorhanden
- ✅ Technische Daten vollständig
- ✅ Fotos hochgeladen (Zähler, HAK, Montageorte)
- ✅ Adresse und Kontaktdaten korrekt

### 3. Zählerschrank-Bewertung
- ✅ Alter des Zählerschranks einschätzen
- ✅ Modernisierungsbedarf erkennen
- ✅ Platz für zusätzliche Komponenten prüfen
- ✅ **Hinweis:** Foto-Analyse wird später implementiert (aktuell nur Metadaten)

### 4. Risiko-Identifikation
- ✅ Potenzielle Installationsprobleme
- ✅ Normkonformität (VDE, TAB)
- ✅ Netzanschlussprobleme
- ✅ Besondere Herausforderungen

### 5. Empfehlungen
- ✅ Konkrete Handlungsempfehlungen
- ✅ Vor-Ort-Termin notwendig?
- ✅ Zusätzliche Informationen erforderlich
- ✅ Nächste Schritte definieren

---

## 📊 JSON Output-Schema

### Hauptstruktur
```json
{
  "agent_type": "arbeitsvorbereiter",
  "version": "1.0",
  "precheck_id": 64,
  "timestamp": "2025-11-21T10:30:00Z",
  "overall_status": "ok | review_needed | not_feasible",
  "plausibility_check": { ... },
  "completeness_check": { ... },
  "meter_cabinet_assessment": { ... },
  "installation_risks": [ ... ],
  "recommendations": [ ... ],
  "summary": "...",
  "next_steps": [ ... ],
  "requires_site_visit": true,
  "estimated_effort_hours": 12.5
}
```

### Detaillierte Felder

#### `overall_status`
- **`ok`**: Projekt kann ohne Bedenken durchgeführt werden
- **`review_needed`**: Rückfragen notwendig, mögliche Probleme
- **`not_feasible`**: Projekt aktuell nicht durchführbar

#### `plausibility_check`
```json
{
  "overall_score": 85,
  "checks": [
    {
      "category": "pv_sizing",
      "passed": true,
      "score": 90,
      "message": "PV-Leistung 8.5 kW passt gut zu EFH",
      "details": "Verhältnis Leistung/Gebäudetyp im optimalen Bereich"
    },
    {
      "category": "storage_sizing",
      "passed": true,
      "score": 85,
      "message": "Speicher 10 kWh gut dimensioniert",
      "details": "Verhältnis Speicher/PV-Leistung = 1.18 (optimal: 1.0-1.5)"
    },
    {
      "category": "main_fuse",
      "passed": true,
      "score": 95,
      "message": "Hauptsicherung 63A ausreichend",
      "details": "Reserve für PV-Einspeisung und Wallbox vorhanden"
    },
    {
      "category": "wallbox_feasibility",
      "passed": true,
      "score": 80,
      "message": "Wallbox 11 kW installierbar",
      "details": "Ausreichend Leistung bei 63A Hauptsicherung"
    },
    {
      "category": "cable_distances",
      "passed": true,
      "score": 90,
      "message": "Kabelstrecken im Normalbereich",
      "details": "WR-Kabel: 12.5m, Wallbox-Kabel: 25m"
    }
  ],
  "issues": [
    "Wallbox-Kabel 25m relativ lang - Spannungsfall prüfen"
  ]
}
```

**Bewertungs-Kategorien:**
- `pv_sizing`: PV-Leistung vs. Gebäudetyp
- `storage_sizing`: Speicher vs. PV-Leistung
- `main_fuse`: Hauptsicherung ausreichend
- `wallbox_feasibility`: Wallbox installierbar
- `cable_distances`: Kabelstrecken realistisch
- `grid_compatibility`: Netzanschluss kompatibel

#### `completeness_check`
```json
{
  "overall_score": 100,
  "all_required_data": true,
  "missing_data": [],
  "checks": {
    "customer_data": {
      "complete": true,
      "fields": ["name", "email", "phone"]
    },
    "site_data": {
      "complete": true,
      "fields": ["address", "building_type", "main_fuse", "grid_type"]
    },
    "photos": {
      "complete": true,
      "uploaded": 4,
      "required_categories": ["meter_cabinet", "hak", "location", "cable_route"],
      "missing_categories": []
    },
    "project_data": {
      "complete": true,
      "fields": ["desired_power", "storage", "wallbox", "inverter_location"]
    }
  }
}
```

#### `meter_cabinet_assessment`
```json
{
  "condition": "modern | acceptable | needs_replacement | unknown",
  "estimated_age": "new | 5-10_years | 10-20_years | 20+_years | unknown",
  "replacement_needed": false,
  "replacement_reason": "",
  "has_space_for_expansion": true,
  "notes": "Basierend auf Foto-Metadaten: Zählerschrank-Foto vorhanden. Detaillierte Bewertung nach Foto-Analyse möglich.",
  "photo_analysis_pending": true,
  "modernization_cost_estimate": null
}
```

**Condition-Werte:**
- `modern`: Moderner Zählerschrank, keine Probleme
- `acceptable`: Funktionsfähig, aber älter
- `needs_replacement`: Modernisierung dringend empfohlen
- `unknown`: Keine Beurteilung möglich (fehlende Daten)

#### `installation_risks`
```json
[
  {
    "category": "cable_routing",
    "severity": "medium",
    "description": "Kabelweg von 25m zur Wallbox",
    "impact": "Höhere Installationskosten, Spannungsfall prüfen",
    "recommendation": "Vor-Ort-Termin zur Routenplanung",
    "estimated_additional_cost": 350.00
  },
  {
    "category": "grid_operator",
    "severity": "low",
    "description": "Netzbetreiber: HamburgNetze",
    "impact": "Standardprozess, keine Besonderheiten",
    "recommendation": "Netzanmeldung nach Angebotsannahme",
    "estimated_additional_cost": 0.00
  }
]
```

**Severity-Stufen:**
- `low`: Keine wesentliche Auswirkung
- `medium`: Erhöhter Aufwand, planbar
- `high`: Kritisches Problem, Projektgefährdung

**Risk-Kategorien:**
- `cable_routing`: Kabelverlegung problematisch
- `main_fuse_upgrade`: Hauptsicherung zu klein
- `meter_cabinet_space`: Kein Platz im Zählerschrank
- `grid_operator`: Netzbetreiber-spezifische Probleme
- `grounding`: Erdung/Potentialausgleich fehlt
- `building_structure`: Gebäude-bedingte Probleme
- `wallbox_installation`: Wallbox-spezifische Probleme

#### `recommendations`
```json
[
  {
    "priority": "high",
    "type": "site_visit",
    "title": "Vor-Ort-Termin vereinbaren",
    "description": "Kunde wünscht Vor-Ort-Termin (siehe Notizen). Zählerschrank und Kabelwege prüfen.",
    "reason": "Kundenwunsch + 25m Wallbox-Kabelstrecke",
    "assigned_to": "sales_team"
  },
  {
    "priority": "medium",
    "type": "component_check",
    "title": "Fronius Wechselrichter-Verfügbarkeit prüfen",
    "description": "Kunde fragt nach Fronius Wechselrichter (siehe Notizen)",
    "reason": "Kundenwunsch aus customer_notes",
    "assigned_to": "quote_agent"
  },
  {
    "priority": "low",
    "type": "documentation",
    "title": "Backup-Power Konzept erstellen",
    "description": "Kunde benötigt Notstromfunktion",
    "reason": "requires_backup_power = true",
    "assigned_to": "technical_planning"
  }
]
```

**Priority-Stufen:**
- `critical`: Sofortiger Handlungsbedarf
- `high`: Zeitnah bearbeiten
- `medium`: Normal priorisiert
- `low`: Bei Gelegenheit

**Recommendation-Types:**
- `site_visit`: Vor-Ort-Termin
- `customer_contact`: Rückfrage beim Kunden
- `component_check`: Komponenten-Verfügbarkeit
- `price_adjustment`: Preisanpassung notwendig
- `documentation`: Dokumentation/Konzept
- `technical_planning`: Technische Detailplanung

#### `summary`
```text
"Projekt-Bewertung für PV-Anlage EFH Hamburg (Precheck #64):

POSITIV:
✓ Technisch gut geplant: 8.5 kW PV + 10 kWh Speicher + 11 kW Wallbox
✓ Hauptsicherung 63A ausreichend dimensioniert
✓ Alle erforderlichen Daten und Fotos vorhanden
✓ 3-Phasen-Netz, Erdung vorhanden
✓ Standardgebiet Hamburg (Netzbetreiber: HamburgNetze)

ZU BEACHTEN:
⚠ Wallbox-Kabelstrecke 25m - Spannungsfall vor Ort prüfen
⚠ Kunde wünscht Fronius Wechselrichter - Verfügbarkeit klären
⚠ Notstromfunktion gewünscht - Backup-Konzept erforderlich
⚠ Kunde bittet um Vor-Ort-Termin

EMPFEHLUNG:
→ Vor-Ort-Termin vereinbaren (Kundenwunsch + Kabelrouten-Prüfung)
→ Angebot mit Fronius-Komponenten erstellen
→ Backup-Power Konzept ergänzen
→ Projekt kann durchgeführt werden (Status: REVIEW_NEEDED wegen Kundenwunsch Vor-Ort-Termin)"
```

#### `next_steps`
```json
[
  {
    "step": 1,
    "action": "site_visit_scheduling",
    "description": "Vor-Ort-Termin mit Kunde vereinbaren",
    "responsible": "sales_team",
    "priority": "high",
    "estimated_duration_days": 3
  },
  {
    "step": 2,
    "action": "quote_preparation",
    "description": "Angebot mit Fronius-Komponenten erstellen",
    "responsible": "quote_agent",
    "priority": "high",
    "estimated_duration_days": 1,
    "dependencies": ["site_visit_scheduling"]
  },
  {
    "step": 3,
    "action": "customer_communication",
    "description": "Terminbestätigung und Projektdetails per E-Mail",
    "responsible": "correspondence_agent",
    "priority": "medium",
    "estimated_duration_days": 1,
    "dependencies": ["quote_preparation"]
  }
]
```

---

## 🤖 Prompt für OpenAI/Claude Node in N8n

### System Prompt
```
Du bist ein erfahrener Arbeitsvorbereiter und Experte für Elektroinstallationen im Bereich Photovoltaik-Anlagen.

DEINE AUFGABE:
Bewerte die vorliegenden Projekt-Daten eines Kunden für eine PV-Anlage und erstelle eine strukturierte technische Bewertung.

DEINE EXPERTISE:
- 15+ Jahre Erfahrung in Elektroinstallation
- Spezialisierung: PV-Anlagen, Speichersysteme, Wallboxen
- Kenntnisse: VDE-Normen, TAB (Technische Anschlussbedingungen), DIN-Normen
- Praxiserfahrung: 500+ PV-Projekte erfolgreich umgesetzt

BEWERTUNGS-KRITERIEN:

1. PLAUSIBILITÄT (0-100 Punkte):
   - PV-Leistung passend zur Gebäudegröße
   - Speichergröße im Verhältnis zur PV-Leistung (optimal: 1.0-1.5)
   - Hauptsicherung ausreichend (Faustregel: PV+Wallbox+Haushalt < 0.7 * Hauptsicherung)
   - Kabelstrecken realistisch (WR: bis 30m normal, Wallbox: bis 40m möglich)
   - Wallbox-Leistung installierbar

2. VOLLSTÄNDIGKEIT (0-100 Punkte):
   - Kundendaten: Name, E-Mail, Telefon
   - Standortdaten: Adresse, Gebäudetyp, Hauptsicherung, Netzart
   - Fotos: Zählerschrank, HAK, Montageorte, Kabelwege
   - Projektdaten: Leistung, Speicher, Wallbox, Standorte

3. ZÄHLERSCHRANK (aktuell ohne Foto-Analyse):
   - Status: unknown (Foto-Analyse später)
   - Hinweis geben: "Detaillierte Bewertung nach Foto-Analyse"

4. RISIKEN identifizieren:
   - Severity: low (grün), medium (gelb), high (rot)
   - Kategorien: Kabelwege, Hauptsicherung, Platzmangel, Netzbetreiber, Erdung

5. EMPFEHLUNGEN:
   - Konkret und umsetzbar
   - Priority: critical, high, medium, low
   - Assigned_to: sales_team, quote_agent, correspondence_agent, technical_planning

6. KUNDENWÜNSCHE berücksichtigen:
   - customer_notes genau lesen
   - Besondere Wünsche (z.B. Hersteller) in Empfehlungen aufnehmen

OUTPUT:
Erstelle eine JSON-Antwort gemäß dem vorgegebenen Schema (siehe Dokumentation).
Achte auf:
- Präzise technische Bewertung
- Verständliche Formulierungen für nachfolgende Agenten
- Konkrete Handlungsempfehlungen
- Realistische Aufwandsschätzungen
```

### User Prompt (Template für N8n)
```
Bewerte folgende PV-Projekt-Daten:

PRECHECK-ID: {{ $json.body.precheck_id }}

KUNDENDATEN:
{{ JSON.stringify($('HTTP Request').item.json.customer, null, 2) }}

STANDORTDATEN:
{{ JSON.stringify($('HTTP Request').item.json.site, null, 2) }}

PROJEKTDATEN:
{{ JSON.stringify($('HTTP Request').item.json.project, null, 2) }}

PREISDATEN:
{{ JSON.stringify($('HTTP Request').item.json.pricing, null, 2) }}

VOLLSTÄNDIGKEIT:
{{ JSON.stringify($('HTTP Request').item.json.completeness, null, 2) }}

METADATEN:
{{ JSON.stringify($('HTTP Request').item.json.metadata, null, 2) }}

---

Erstelle eine strukturierte Bewertung als JSON gemäß Schema.
Besondere Aufmerksamkeit auf:
- customer_notes (Kundenwünsche)
- Kabelstrecken (distance_meter_to_inverter, wallbox_cable_length)
- Hauptsicherung vs. Gesamtleistung
- Vollständigkeit der Daten

WICHTIG: Antworte NUR mit gültigem JSON, keine Markdown-Code-Blöcke!
```

---

## 🔧 N8n Workflow Integration

### Node-Struktur

```
1. [Webhook Trigger] - Empfängt precheck_submitted Event
   ↓
2. [HTTP Request] - Holt Precheck-Daten von Django API
   URL: {{ $json.body.api_base_url }}{{ $json.body.api_endpoints.precheck_data }}
   Headers: X-API-Key: {{ $env.DJANGO_API_KEY }}
   ↓
3. [OpenAI/Claude] - Arbeitsvorbereiter Agent
   Model: gpt-4 oder claude-3-opus
   System Prompt: [siehe oben]
   User Prompt: [siehe oben]
   Temperature: 0.3 (präzise technische Bewertung)
   Max Tokens: 4000
   Response Format: JSON
   ↓
4. [Code Node] - Parse & Validiere Agent-Output
   ↓
5. [Switch] - Verzweigung basierend auf overall_status
   - ok → Quote Agent
   - review_needed → Sales Notification
   - not_feasible → Customer Rejection Email
   ↓
6. [Set Variable] - Speichert Arbeitsvorbereiter-Output für nachfolgende Nodes
   agent_arbeitsvorbereiter_output: {{ $json }}
```

### Node-Konfiguration: OpenAI/Claude

**Option A: OpenAI (gpt-4)**
```
Model: gpt-4-turbo-preview
System Message: [System Prompt siehe oben]
User Message: [User Prompt siehe oben]
Temperature: 0.3
Maximum Tokens: 4000
Response Format: json_object
```

**Option B: Claude (Anthropic)**
```
Model: claude-3-opus-20240229
System: [System Prompt siehe oben]
Messages:
  - role: user
    content: [User Prompt siehe oben]
Temperature: 0.3
Max Tokens: 4000
```

### Code Node: Parse & Validierung

```javascript
// Parse KI-Antwort
const inputData = $input.first().json;

let assessment;
if (Array.isArray(inputData)) {
  assessment = inputData[0]?.message?.content;
} else if (inputData.choices) {
  assessment = inputData.choices[0]?.message?.content;
} else if (inputData.message?.content) {
  assessment = inputData.message.content;
} else if (typeof inputData === 'object' && inputData.agent_type) {
  // Bereits geparst
  assessment = inputData;
}

// Parse JSON falls String
let assessmentData;
if (typeof assessment === 'string') {
  try {
    // Remove markdown code blocks if present
    const jsonMatch = assessment.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      assessmentData = JSON.parse(jsonMatch[1]);
    } else {
      assessmentData = JSON.parse(assessment.trim());
    }
  } catch (e) {
    throw new Error(`Parse-Fehler: ${e.message}\nRaw: ${assessment.substring(0, 200)}`);
  }
} else {
  assessmentData = assessment;
}

// Validierung
const required = ['agent_type', 'overall_status', 'plausibility_check', 'recommendations'];
const missing = required.filter(field => !assessmentData[field]);
if (missing.length > 0) {
  throw new Error(`Fehlende Pflichtfelder: ${missing.join(', ')}`);
}

// Bereichere mit Metadaten
assessmentData.processed_at = new Date().toISOString();

return { json: assessmentData };
```

### Fehlerbehandlung
```
Error Handler Node:
- Bei API-Fehler: Retry 3x mit 5s Delay
- Bei Timeout: Manuelles Review triggern
- Bei ungültigem JSON: Fallback-Bewertung erstellen
```

---

## 📊 Bewertungs-Logik im Detail

### 1. Plausibilitäts-Scores

#### PV-Sizing Score
```javascript
function calculatePVSizingScore(desired_power_kw, building_type) {
  const ranges = {
    'efh': { min: 4, max: 15, optimal_min: 6, optimal_max: 12 },
    'mfh': { min: 8, max: 30, optimal_min: 12, optimal_max: 25 },
    'commercial': { min: 15, max: 100, optimal_min: 25, optimal_max: 75 }
  };

  const range = ranges[building_type] || ranges['efh'];

  if (desired_power_kw >= range.optimal_min && desired_power_kw <= range.optimal_max) {
    return 95; // Optimal
  }
  if (desired_power_kw >= range.min && desired_power_kw <= range.max) {
    return 70; // Akzeptabel
  }
  return 40; // Problematisch
}
```

#### Storage-Sizing Score
```javascript
function calculateStorageSizingScore(desired_power_kw, storage_kwh) {
  if (storage_kwh === 0) return 100; // Kein Speicher = keine Bewertung

  const ratio = storage_kwh / desired_power_kw;

  if (ratio >= 1.0 && ratio <= 1.5) return 95;  // Optimal
  if (ratio >= 0.8 && ratio <= 2.0) return 80;  // Gut
  if (ratio >= 0.5 && ratio <= 3.0) return 60;  // Akzeptabel
  return 40; // Problematisch
}
```

#### Main-Fuse Score
```javascript
function calculateMainFuseScore(main_fuse_ampere, desired_power_kw, has_wallbox, wallbox_class) {
  // Berechne Gesamtleistung
  let total_power_kw = desired_power_kw;

  if (has_wallbox) {
    const wallbox_power = {
      '4kw': 4,
      '11kw': 11,
      '22kw': 22
    };
    total_power_kw += wallbox_power[wallbox_class] || 0;
  }

  // Durchschnittlicher Haushaltsverbrauch
  const household_peak_kw = 5;
  total_power_kw += household_peak_kw;

  // Berechne maximalen Strom (3-Phasen: P = sqrt(3) * U * I)
  const max_current = (total_power_kw * 1000) / (Math.sqrt(3) * 230);

  // Sicherheitsfaktor 0.7 (70% Auslastung max)
  const required_fuse = max_current / 0.7;

  if (main_fuse_ampere >= required_fuse * 1.2) return 100; // Sehr gut
  if (main_fuse_ampere >= required_fuse) return 85;       // Gut
  if (main_fuse_ampere >= required_fuse * 0.9) return 60; // Knapp
  return 30; // Zu klein
}
```

### 2. Vollständigkeits-Scores

```javascript
function calculateCompletenessScore(completeness) {
  const required_checks = [
    'has_customer_data',
    'has_customer_email',
    'has_customer_phone',
    'has_site_data',
    'has_site_address',
    'has_main_fuse',
    'has_grid_type',
    'has_photos',
    'has_meter_photo',
    'has_hak_photo',
    'has_power_data',
    'has_inverter_location',
    'has_distance_data'
  ];

  let passed = 0;
  required_checks.forEach(check => {
    if (completeness[check] === true) passed++;
  });

  return Math.round((passed / required_checks.length) * 100);
}
```

### 3. Risk-Detection Logik

```javascript
function detectInstallationRisks(precheck_data) {
  const risks = [];

  // Kabelstrecken-Risiko
  if (precheck_data.project.distance_meter_to_inverter > 30) {
    risks.push({
      category: 'cable_routing',
      severity: 'medium',
      description: `WR-Kabelstrecke ${precheck_data.project.distance_meter_to_inverter}m (> 30m)`,
      impact: 'Höherer Spannungsfall, dickere Kabel erforderlich',
      recommendation: 'Kabelquerschnitt berechnen, ggf. Zwischenverteilung',
      estimated_additional_cost: (precheck_data.project.distance_meter_to_inverter - 30) * 15
    });
  }

  if (precheck_data.project.wallbox_cable_length > 40) {
    risks.push({
      category: 'wallbox_installation',
      severity: 'high',
      description: `Wallbox-Kabelstrecke ${precheck_data.project.wallbox_cable_length}m (> 40m)`,
      impact: 'Kritischer Spannungsfall, spezielle Kabelführung notwendig',
      recommendation: 'Alternative Standort prüfen oder Ladeleistung reduzieren',
      estimated_additional_cost: 500
    });
  }

  // Hauptsicherungs-Risiko
  const fuse_score = calculateMainFuseScore(...);
  if (fuse_score < 60) {
    risks.push({
      category: 'main_fuse_upgrade',
      severity: 'high',
      description: 'Hauptsicherung zu klein dimensioniert',
      impact: 'Upgrade durch Netzbetreiber erforderlich',
      recommendation: 'Netzanschluss-Upgrade beauftragen (4-8 Wochen Vorlaufzeit)',
      estimated_additional_cost: 1500
    });
  }

  // Erdungs-Risiko
  if (precheck_data.project.has_grounding.value === 'no') {
    risks.push({
      category: 'grounding',
      severity: 'high',
      description: 'Keine Erdung vorhanden',
      impact: 'Erdungsanlage muss nachgerüstet werden',
      recommendation: 'Erdungsstäbe setzen, Potentialausgleich herstellen',
      estimated_additional_cost: 800
    });
  }

  return risks;
}
```

### 4. Overall-Status Bestimmung

```javascript
function determineOverallStatus(plausibility_score, completeness_score, risks, has_customer_notes) {
  // Critical risks = not_feasible
  const critical_risks = risks.filter(r => r.severity === 'high');
  if (critical_risks.length > 2) return 'not_feasible';

  // Low scores = review_needed
  if (plausibility_score < 60 || completeness_score < 80) return 'review_needed';

  // Customer notes with special requests = review_needed
  if (has_customer_notes && (
    has_customer_notes.includes('Vor-Ort') ||
    has_customer_notes.includes('Termin') ||
    has_customer_notes.includes('Fronius') ||
    has_customer_notes.includes('spezielle')
  )) {
    return 'review_needed';
  }

  // Medium risks = review_needed
  if (risks.filter(r => r.severity === 'medium').length > 0) return 'review_needed';

  // All good = ok
  return 'ok';
}
```

---

## 📝 Beispiel-Output (Vollständig)

```json
{
  "agent_type": "arbeitsvorbereiter",
  "version": "1.0",
  "precheck_id": 64,
  "timestamp": "2025-11-21T10:45:23Z",
  "overall_status": "review_needed",
  "plausibility_check": {
    "overall_score": 82,
    "checks": [
      {
        "category": "pv_sizing",
        "passed": true,
        "score": 90,
        "message": "PV-Leistung 8.5 kW passt gut zu Einfamilienhaus",
        "details": "Leistung im optimalen Bereich (6-12 kW für EFH)"
      },
      {
        "category": "storage_sizing",
        "passed": true,
        "score": 85,
        "message": "Speicher 10 kWh gut dimensioniert",
        "details": "Verhältnis Speicher/PV = 1.18 (optimal: 1.0-1.5)"
      },
      {
        "category": "main_fuse",
        "passed": true,
        "score": 95,
        "message": "Hauptsicherung 63A sehr gut dimensioniert",
        "details": "Benötigt ca. 45A (PV 8.5kW + Wallbox 11kW + Haushalt 5kW), Reserve vorhanden"
      },
      {
        "category": "wallbox_feasibility",
        "passed": true,
        "score": 80,
        "message": "Wallbox 11 kW installierbar",
        "details": "Ausreichend Leistung, aber Kabelstrecke 25m beachten"
      },
      {
        "category": "cable_distances",
        "passed": true,
        "score": 70,
        "message": "Kabelstrecken im akzeptablen Bereich",
        "details": "WR: 12.5m (normal), Wallbox: 25m (lang, aber machbar)"
      }
    ],
    "issues": [
      "Wallbox-Kabel 25m - Spannungsfall vor Ort prüfen",
      "Kundenwunsch Fronius - Verfügbarkeit klären"
    ]
  },
  "completeness_check": {
    "overall_score": 100,
    "all_required_data": true,
    "missing_data": [],
    "checks": {
      "customer_data": {
        "complete": true,
        "fields": ["name", "email", "phone"]
      },
      "site_data": {
        "complete": true,
        "fields": ["address", "building_type", "main_fuse", "grid_type"]
      },
      "photos": {
        "complete": true,
        "uploaded": 4,
        "required_categories": ["meter_cabinet", "hak", "location", "cable_route"],
        "missing_categories": []
      },
      "project_data": {
        "complete": true,
        "fields": ["desired_power", "storage", "wallbox", "inverter_location"]
      }
    }
  },
  "meter_cabinet_assessment": {
    "condition": "unknown",
    "estimated_age": "unknown",
    "replacement_needed": false,
    "replacement_reason": "",
    "has_space_for_expansion": true,
    "notes": "Zählerschrank-Foto vorhanden (meter_cabinet). Detaillierte Bewertung nach Foto-Analyse möglich. Aktuell keine Hinweise auf Probleme.",
    "photo_analysis_pending": true,
    "modernization_cost_estimate": null
  },
  "installation_risks": [
    {
      "category": "cable_routing",
      "severity": "medium",
      "description": "Wallbox-Kabelstrecke 25m relativ lang",
      "impact": "Erhöhter Spannungsfall möglich, dickerer Kabelquerschnitt notwendig (6mm² statt 4mm²)",
      "recommendation": "Vor-Ort-Termin zur Kabelrouten-Prüfung, ggf. Zwischenabzweig planen",
      "estimated_additional_cost": 200.00
    },
    {
      "category": "component_check",
      "severity": "low",
      "description": "Kundenwunsch: Fronius Wechselrichter",
      "impact": "Mögliche Lieferzeit oder Preisabweichung",
      "recommendation": "Verfügbarkeit und Preis für Fronius WR prüfen",
      "estimated_additional_cost": 0.00
    },
    {
      "category": "grid_operator",
      "severity": "low",
      "description": "Netzbetreiber: HamburgNetze",
      "impact": "Standardprozess, keine Besonderheiten bekannt",
      "recommendation": "Netzanmeldung nach Angebotsannahme durchführen",
      "estimated_additional_cost": 0.00
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "type": "site_visit",
      "title": "Vor-Ort-Termin vereinbaren",
      "description": "Kunde wünscht explizit Vor-Ort-Termin (siehe customer_notes). Nutzen für Prüfung: Zählerschrank-Zustand, Kabelrouten (insbes. 25m Wallbox), Montageorte.",
      "reason": "Kundenwunsch + technische Prüfung Kabelwege",
      "assigned_to": "sales_team"
    },
    {
      "priority": "high",
      "type": "component_check",
      "title": "Fronius Wechselrichter-Verfügbarkeit prüfen",
      "description": "Kunde fragt nach Fronius Wechselrichter (siehe customer_notes). Prüfen: Verfügbarkeit, Lieferzeit, Preisdifferenz zu Standard-WR.",
      "reason": "Kundenwunsch aus customer_notes",
      "assigned_to": "quote_agent"
    },
    {
      "priority": "medium",
      "type": "documentation",
      "title": "Backup-Power Konzept erstellen",
      "description": "Kunde benötigt Notstromfunktion (requires_backup_power = true). Konzept für Ersatzstromversorgung mit Speicher erstellen.",
      "reason": "Projektanforderung",
      "assigned_to": "technical_planning"
    },
    {
      "priority": "medium",
      "type": "technical_planning",
      "title": "Wallbox-Kabelführung detaillieren",
      "description": "25m Kabelstrecke zur Wallbox: Kabelquerschnitt berechnen (mindestens 6mm²), Routenplanung, ggf. Leerrohre.",
      "reason": "Technische Anforderung",
      "assigned_to": "technical_planning"
    },
    {
      "priority": "low",
      "type": "customer_contact",
      "title": "PV-Überschuss-Laden Wallbox erklären",
      "description": "Kunde wünscht PV-Überschuss-Laden (wallbox_pv_surplus = true). In Angebot/Gespräch Funktion erklären.",
      "reason": "Kundenverständnis sicherstellen",
      "assigned_to": "correspondence_agent"
    }
  ],
  "summary": "Projekt-Bewertung PV-Anlage Einfamilienhaus Hamburg (Precheck #64):\n\n✅ POSITIV:\n• Technisch sehr gut geplant: 8.5 kW PV + 10 kWh Speicher + 11 kW Wallbox\n• Hauptsicherung 63A ausreichend dimensioniert (ca. 45A benötigt, gute Reserve)\n• Alle erforderlichen Daten vollständig (100% Completeness)\n• 4 Fotos hochgeladen (Zähler, HAK, Montageorte, Kabelwege)\n• 3-Phasen-Netz, Erdung und Tiefenerde vorhanden\n• Standardgebiet Hamburg mit bekanntem Netzbetreiber (HamburgNetze)\n• Speicher/PV-Verhältnis optimal (1.18)\n\n⚠️ ZU BEACHTEN:\n• Wallbox-Kabelstrecke 25m relativ lang - Spannungsfall vor Ort prüfen, dickerer Querschnitt (6mm²) erforderlich\n• Kunde wünscht Fronius Wechselrichter - Verfügbarkeit und Preisdifferenz klären\n• Notstromfunktion gewünscht (Backup Power) - Konzept mit Speicher erstellen\n• Kunde bittet explizit um Vor-Ort-Termin (siehe customer_notes)\n• Zählerschrank-Foto vorhanden, aber detaillierte Bewertung steht noch aus (Foto-Analyse)\n\n💡 EMPFEHLUNG:\n→ Vor-Ort-Termin vereinbaren (Kundenwunsch + Kabelrouten-Prüfung + Zählerschrank-Bewertung)\n→ Angebot mit Fronius-Komponenten erstellen (falls verfügbar)\n→ Backup-Power Konzept ergänzen (Notstrom mit Speicher)\n→ Wallbox-Kabelführung detailliert planen (6mm² Kabel, Routenoptimierung)\n\n📊 STATUS: REVIEW_NEEDED\nGrund: Kundenwunsch Vor-Ort-Termin + spezielle Anforderungen (Fronius, Backup-Power)\n\n✅ Projekt ist technisch durchführbar und gut geplant. Nach Klärung der offenen Punkte (Vor-Ort-Termin, Fronius-Verfügbarkeit) kann Angebot erstellt werden.",
  "next_steps": [
    {
      "step": 1,
      "action": "site_visit_scheduling",
      "description": "Vor-Ort-Termin mit Kunde Max Mustermann vereinbaren (E-Mail: max.mustermann.test@example.com, Tel: +49 40 12345678)",
      "responsible": "sales_team",
      "priority": "high",
      "estimated_duration_days": 3
    },
    {
      "step": 2,
      "action": "component_availability_check",
      "description": "Fronius Wechselrichter 8.5 kW Verfügbarkeit, Lieferzeit und Preis prüfen",
      "responsible": "procurement",
      "priority": "high",
      "estimated_duration_days": 1,
      "dependencies": []
    },
    {
      "step": 3,
      "action": "technical_planning",
      "description": "Wallbox-Kabelführung planen: 25m Route, Kabelquerschnitt 6mm², Spannungsfall berechnen",
      "responsible": "technical_planning",
      "priority": "medium",
      "estimated_duration_days": 2,
      "dependencies": ["site_visit_scheduling"]
    },
    {
      "step": 4,
      "action": "quote_preparation",
      "description": "Angebot erstellen mit Fronius WR, Backup-Power Funktion, detaillierter Wallbox-Installation",
      "responsible": "quote_agent",
      "priority": "high",
      "estimated_duration_days": 2,
      "dependencies": ["site_visit_scheduling", "component_availability_check"]
    },
    {
      "step": 5,
      "action": "customer_communication",
      "description": "Terminbestätigung, Projektdetails und Angebot per E-Mail senden",
      "responsible": "correspondence_agent",
      "priority": "medium",
      "estimated_duration_days": 1,
      "dependencies": ["quote_preparation"]
    }
  ],
  "requires_site_visit": true,
  "estimated_effort_hours": 14.5,
  "estimated_project_duration_days": 35
}
```

---

## 🧪 Testing & Validierung

### Test-Cases

#### Test 1: Optimal-Projekt
```json
Input:
- EFH, 8kW PV, 10kWh Speicher, 63A Hauptsicherung
- Alle Daten vollständig, Fotos vorhanden
- Keine besonderen Kundenwünsche

Expected Output:
- overall_status: "ok"
- plausibility_score: > 85
- completeness_score: 100
- installation_risks: [] oder nur "low" severity
```

#### Test 2: Review-Bedarf
```json
Input:
- EFH, 12kW PV, keine Speicher, 35A Hauptsicherung
- Wallbox 22kW gewünscht
- Kabelstrecke 45m

Expected Output:
- overall_status: "review_needed"
- plausibility_score: < 70
- installation_risks: 2-3 "medium" oder "high" risks
- recommendations: Hauptsicherungs-Upgrade, Kabelrouten-Prüfung
```

#### Test 3: Nicht durchführbar
```json
Input:
- Gewerbe, 50kW PV, 63A Hauptsicherung
- Keine Erdung vorhanden
- TT-Netz, Kabelstrecke 80m

Expected Output:
- overall_status: "not_feasible"
- plausibility_score: < 50
- installation_risks: 3+ "high" severity
- recommendations: Grundlegende Infrastruktur-Updates
```

### Validierungs-Checkliste
- [ ] JSON-Schema korrekt (alle Pflichtfelder)
- [ ] Scores im Bereich 0-100
- [ ] Severity nur: low, medium, high
- [ ] Priority nur: critical, high, medium, low
- [ ] Overall_status nur: ok, review_needed, not_feasible
- [ ] Timestamps im ISO 8601 Format
- [ ] Estimated_additional_cost als Number (2 Dezimalstellen)
- [ ] Next_steps sortiert nach dependencies

---

## 📚 Weiterführende Informationen

### Referenzen
- VDE-AR-N 4105: Erzeugungsanlagen am Niederspannungsnetz
- TAB Netzbetreiber: Technische Anschlussbedingungen
- DIN VDE 0100: Errichten von Niederspannungsanlagen
- KfW 442: Wallbox-Förderrichtlinien

### Nachfolgende Agenten
1. **Quote Agent** (Angebotersteller)
   - Input: Arbeitsvorbereiter-Output
   - Task: Detailliertes Angebot erstellen
   - Output: Quote-Dokument (PDF)

2. **Correspondence Agent** (Kundenkommunikation)
   - Input: Arbeitsvorbereiter-Output + Quote
   - Task: E-Mails verfassen, Fragen beantworten
   - Output: E-Mail-Texte, Terminvorschläge

3. **Technical Planning Agent** (später)
   - Input: Arbeitsvorbereiter-Output + genehmigte Quote
   - Task: Detaillierte Installationsplanung
   - Output: Schaltpläne, Materiallisten

---

## 📝 Version History

### Version 1.0 (2025-11-21)
- ✅ Initiale Version
- ✅ JSON-Schema definiert
- ✅ Prompt erstellt
- ✅ Bewertungslogik dokumentiert
- ✅ Beispiel-Output erstellt
- ⚠️ Foto-Analyse: Vorbereitet, aber noch nicht implementiert

### Geplante Erweiterungen
- [ ] Version 1.1: Foto-Analyse Integration (Vision AI)
- [ ] Version 1.2: Historische Daten-Analyse (Lernkurve)
- [ ] Version 1.3: Preisoptimierungs-Vorschläge
- [ ] Version 2.0: Multi-Agenten Diskussion (Agent-zu-Agent Feedback)

---

**Dokumentiert von:** Claude Code (Anthropic)
**Datum:** 2025-11-21
**Projekt:** EDGARD Elektro PV-Service
**Status:** ✅ Bereit für N8n Integration
