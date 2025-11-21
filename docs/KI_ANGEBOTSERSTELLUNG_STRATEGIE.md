# KI-Angebotserstellung: Strategieempfehlung

**Projekt:** EDGARD Elektro PV-Service
**Ziel:** Automatische Angebotserstellung mit KI und n8n
**Status:** Konzept & Implementierungsempfehlung
**Erstellt:** 2025-11-20

---

## 🎯 Ausgangssituation

**Du hast:**
- ✅ Kundendaten aus Precheck (API: `/api/integrations/precheck/<id>/`)
- ✅ Preistabelle/Produktkatalog (API: `/api/integrations/pricing/`)
- ✅ Technische Daten (WR-Leistung, Speicher, Wallbox, Fotos)
- ✅ n8n Workflow-Engine
- ✅ OpenAI/Claude API-Zugang

**Du brauchst:**
- 📄 Ein strukturiertes, professionelles Angebot (PDF)
- 🧠 KI-Unterstützung für intelligente Produktauswahl
- 📚 Wissensdatenbank für KI (Produktinformationen, Best Practices)

---

## 🏆 Empfohlener Ansatz: Hybrid-Modell

Kombination aus **strukturierter Logik** + **KI-Optimierung**

```
┌─────────────────────────────────────────────────────────┐
│                    WORKFLOW-ARCHITEKTUR                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. PRECHECK-DATEN ABRUFEN                              │
│     → Kunde, Standort, System, Fotos                    │
│                                                          │
│  2. BASISPRODUKTE ERMITTELN (Django Pricing Engine)     │
│     → Wechselrichter (basierend auf kW)                 │
│     → Speicher (falls gewählt)                          │
│     → Wallbox (falls gewählt)                           │
│     → Kabel, Montage, etc.                              │
│                                                          │
│  3. PRODUKTKATALOG ABRUFEN (API)                        │
│     → Alle verfügbaren Produkte + Preise               │
│                                                          │
│  4. KI-OPTIMIERUNG (GPT-4 / Claude)                     │
│     ├─ Produktauswahl verfeinern                        │
│     ├─ Zusatzprodukte empfehlen                         │
│     ├─ Angebots-Text generieren                         │
│     └─ Kundenspezifische Anpassungen                    │
│                                                          │
│  5. ANGEBOT ERSTELLEN (Django)                          │
│     → POST /api/quotes/create-from-precheck/            │
│     → Speichert Quote + Items in Datenbank             │
│                                                          │
│  6. PDF GENERIEREN (Django)                             │
│     → WeasyPrint/ReportLab                              │
│     → Professionelles Layout                            │
│                                                          │
│  7. E-MAIL VERSAND                                      │
│     → PDF als Anhang                                    │
│     → Personalisierte Nachricht                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Wissensdatenbank-Ansätze (3 Optionen)

### **Option 1: RAG mit Vektordatenbank** ⭐ **EMPFOHLEN für Skalierung**

**Konzept:** Textdokumente werden in Vektoren umgewandelt und in spezieller Datenbank gespeichert. KI kann dann relevante Informationen abrufen.

**Tools:**
- **Pinecone** (Cloud, einfach) - $70/Monat für 100k Vektoren
- **Qdrant** (Self-Hosted, kostenlos) - Lokal auf deinem Server
- **Chroma** (Einfachste Option) - Python-Library

**Vorteile:**
- ✅ Skalierbar (unbegrenzt Dokumente)
- ✅ Semantische Suche (versteht Bedeutung, nicht nur Keywords)
- ✅ Automatische Updates möglich
- ✅ Mehrere Wissensquellen kombinierbar

**Nachteile:**
- ❌ Zusätzliche Infrastruktur
- ❌ Höhere Komplexität
- ❌ Setup-Zeit: 2-3 Tage

**Implementierung:**

```python
# 1. Dokumente vorbereiten
knowledge_base = {
    "products": [
        {
            "name": "Fronius Symo 8.2-3-M",
            "category": "Wechselrichter",
            "power": "8.2 kW",
            "phases": 3,
            "features": "WLAN, Datenlogger, 99% Wirkungsgrad",
            "compatibility": ["Fronius Solar Battery", "BYD HVM"],
            "installation_notes": "Mindestens 30cm Abstand zu Wand",
            "warranty": "10 Jahre, erweiterbar auf 20",
            "best_for": "Einfamilienhäuser 6-10 kWp"
        }
        # ... weitere Produkte
    ],
    "installation_guidelines": [
        {
            "title": "Zählerschrank-Ertüchtigung",
            "content": "Bei Altbauten vor 1990 ist häufig...",
            "applies_to": ["Hauptsicherung < 35A", "Gebäudetyp: Altbau"]
        }
    ]
}

# 2. In Vektordatenbank laden
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(documents, embeddings)

# 3. In n8n abfragen
# Vector Store Node (mit Langchain-Integration)
# Query: "Welcher Wechselrichter für 8.5kW EFH?"
# → Gibt relevante Produkte zurück
```

**Kosten:**
- Pinecone: ~$70/Monat
- Qdrant (Self-Hosted): Kostenlos
- OpenAI Embeddings: ~$0.0001 pro 1k Tokens (vernachlässigbar)

---

### **Option 2: Kontext-Fenster (In-Prompt)** ⭐ **EMPFOHLEN für Start**

**Konzept:** Alle Produktinformationen werden direkt in den KI-Prompt eingefügt.

**Vorteile:**
- ✅ Einfachste Implementierung (sofort einsetzbar)
- ✅ Keine zusätzliche Infrastruktur
- ✅ Volle Kontrolle über Kontext
- ✅ Setup-Zeit: 1 Stunde

**Nachteile:**
- ❌ Limitiert durch Token-Limit (GPT-4o: 128k Tokens ≈ 50 Produkte detailliert)
- ❌ Höhere API-Kosten bei großem Kontext
- ❌ Manuelle Updates erforderlich

**Implementierung:**

```javascript
// n8n Code Node: Erstelle strukturierten Kontext
const precheckData = $input.item(0).json.precheck_data;
const products = $input.item(1).json.products;

// Kontext aufbauen
const context = {
  available_inverters: products
    .filter(p => p.category === 'Wechselrichter')
    .map(p => ({
      name: p.name,
      power: p.power_kw,
      price_net: p.sales_price_net,
      description: p.description,
      best_for: p.best_for || 'Allgemein'
    })),

  available_storage: products
    .filter(p => p.category === 'Speicher')
    .map(p => ({
      name: p.name,
      capacity_kwh: p.capacity_kwh,
      price_net: p.sales_price_net,
      compatibility: p.compatible_with || []
    })),

  installation_packages: [
    {
      name: "Basis-Paket",
      includes: ["AC-Verkabelung", "Überspannungsschutz", "Inbetriebnahme"],
      price: 890
    },
    {
      name: "Plus-Paket",
      includes: ["Basis + Zählerplatz-Ertüchtigung", "Selektive Sicherung"],
      price: 1490
    },
    {
      name: "Pro-Paket",
      includes: ["Plus + Energiemanagement", "Speicher-Integration"],
      price: 2290
    }
  ]
};

return { json: { context, precheckData } };
```

**OpenAI Prompt:**
```
System: Du bist Angebotsspezialist für PV-Anlagen bei EDGARD Elektro.

VERFÜGBARE PRODUKTE:
${JSON.stringify(context, null, 2)}

KUNDENANFRAGE:
- Kunde: ${precheckData.customer.name}
- Leistung: ${precheckData.project.desired_power_kw} kW
- Speicher: ${precheckData.project.storage_kwh} kWh
- Wallbox: ${precheckData.project.has_wallbox}
- Gebäude: ${precheckData.site.building_type}
- Hauptsicherung: ${precheckData.site.main_fuse_ampere}A

AUFGABE:
1. Wähle passende Produkte aus (Wechselrichter, Speicher, Wallbox)
2. Empfehle Installations-Paket
3. Erstelle Angebots-Text (professionell, ca. 200 Wörter)
4. Liste alle Positionen mit Preisen

ANTWORT als JSON:
{
  "selected_products": [
    {
      "category": "Wechselrichter",
      "product_name": "...",
      "quantity": 1,
      "price_net": 1500.00,
      "reason": "Optimal für 8.5kW Anlage"
    }
  ],
  "installation_package": "Plus-Paket",
  "offer_text": "Sehr geehrte/r ...",
  "total_net": 4500.00,
  "notes": "Besonderheiten beachten..."
}
```

**Kosten:**
- GPT-4o: ~$0.03 pro Angebot (bei 10k Tokens Input + 2k Output)
- GPT-3.5-turbo: ~$0.003 pro Angebot (10x günstiger, 85% Qualität)

---

### **Option 3: Function Calling / Structured Output** ⭐⭐ **BESTE Kombination**

**Konzept:** Kombination aus Option 1+2. KI gibt strukturierte JSON-Antwort zurück, die direkt in Django-API eingefügt werden kann.

**Vorteile:**
- ✅ Strukturierte, validierbare Antworten
- ✅ Keine manuellen Parsing-Fehler
- ✅ Direkt in API integrierbar
- ✅ Beste Balance: Flexibilität + Struktur

**Implementierung:**

```javascript
// n8n OpenAI Node mit Function Calling
{
  "model": "gpt-4o",
  "messages": [...],
  "functions": [
    {
      "name": "create_quote",
      "description": "Erstellt ein PV-Angebot mit ausgewählten Produkten",
      "parameters": {
        "type": "object",
        "properties": {
          "quote_items": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "product_id": {"type": "number"},
                "product_name": {"type": "string"},
                "quantity": {"type": "number"},
                "unit_price_net": {"type": "number"},
                "description": {"type": "string"}
              },
              "required": ["product_id", "quantity", "unit_price_net"]
            }
          },
          "offer_text": {"type": "string"},
          "notes": {"type": "string"},
          "recommended_package": {"type": "string", "enum": ["basis", "plus", "pro"]}
        },
        "required": ["quote_items", "offer_text"]
      }
    }
  ],
  "function_call": {"name": "create_quote"}
}
```

**Vorteil:** KI gibt **garantiert** valides JSON zurück → Direkt an Django API!

---

## 🎯 KONKRETE EMPFEHLUNG für dein Projekt

### **Phase 1: Schnellstart (diese Woche)** ⭐ **START HIER**

**Ansatz:** Option 2 (In-Prompt) + Function Calling (Option 3)

**Workflow:**

```
1. Precheck-Daten + Produktkatalog laden
   ↓
2. Kontext strukturieren (10 relevanteste Produkte)
   ↓
3. OpenAI mit Function Calling
   → Gibt strukturiertes JSON zurück
   ↓
4. Validierung in n8n (Prüfe Pflichtfelder)
   ↓
5. Entwurf erstellen in Django
   POST /api/quotes/create-draft/
   {
     "precheck_id": 66,
     "items": [
       {"product_id": 70, "quantity": 1, "price_net": 1500},
       {"product_id": 85, "quantity": 1, "price_net": 2000}
     ],
     "notes": "KI-generiert, bitte prüfen",
     "status": "draft"
   }
   ↓
6. E-Mail an Team: "Angebots-Entwurf prüfen"
   → Link zum Dashboard
   ↓
7. Manuell freigeben → PDF → Kunde
```

**Vorteile:**
- ✅ In 1-2 Tagen implementierbar
- ✅ Keine zusätzliche Infrastruktur
- ✅ Niedrige Kosten (~$0.03/Angebot)
- ✅ Menschliche Prüfung vor Versand
- ✅ 90% Zeitersparnis vs. manuell

**Kosten:**
- Entwicklung: 8-16 Stunden
- Laufende Kosten: ~$0.03 pro Angebot (GPT-4o) oder $0.003 (GPT-3.5)
- Bei 100 Angeboten/Monat: **$3-30/Monat**

---

### **Phase 2: Skalierung (nächster Monat)** 📈

**Upgrade zu:** RAG mit Vektordatenbank (Option 1)

**Wissensdatenbank-Inhalte:**

1. **Produkt-Datenblätter** (PDFs)
   - Wechselrichter-Specs
   - Speicher-Kompatibilität
   - Installations-Handbücher

2. **Installations-Richtlinien**
   - Best Practices pro Gebäudetyp
   - Kabelverlegung-Regeln
   - Netzanschluss-Anforderungen

3. **Häufige Kundenanfragen** (FAQ)
   - Typische Fragen + Antworten
   - Einwandbehandlung

4. **Angebots-Vorlagen**
   - Erfolgreiche Angebots-Texte
   - Formulierungen pro Kundentyp

**Implementierung mit Qdrant (Self-Hosted):**

```bash
# 1. Qdrant installieren (Docker)
docker run -p 6333:6333 qdrant/qdrant

# 2. Python-Script für Datenbank-Aufbau
pip install qdrant-client langchain openai

# 3. Dokumente laden
python scripts/build_knowledge_base.py
```

**n8n Integration:**

```javascript
// HTTP Request an Qdrant
{
  "method": "POST",
  "url": "http://localhost:6333/collections/pv-knowledge/points/search",
  "body": {
    "vector": [0.1, 0.2, ...],  // Von OpenAI Embeddings
    "limit": 5,
    "with_payload": true
  }
}
// → Gibt 5 relevanteste Dokumente zurück
```

**Vorteile:**
- ✅ Unbegrenzt skalierbar
- ✅ Automatische Updates (neue Produkte → Auto-Index)
- ✅ Mehrsprachig möglich
- ✅ Bessere KI-Antworten durch mehr Kontext

**Kosten:**
- Qdrant (Self-Hosted): **Kostenlos**
- Embeddings: ~$0.0001 pro Dokument (einmalig)
- Laufende Kosten: Gleich wie Phase 1

---

## 📊 Kosten-Nutzen-Vergleich

| Ansatz | Setup-Zeit | Kosten/Monat | Qualität | Skalierbar | Empfehlung |
|--------|-----------|--------------|----------|------------|------------|
| **Manuell** | - | 0€ | 100% | ❌ | Baseline |
| **Option 2 (In-Prompt)** | 1-2 Tage | 3-30€ | 85% | ⚠️ Limitiert | ⭐ **START** |
| **Option 3 (+ Function Call)** | 2-3 Tage | 3-30€ | 90% | ⚠️ Limitiert | ⭐⭐ **IDEAL** |
| **Option 1 (RAG)** | 3-5 Tage | 3-100€ | 95% | ✅ Unbegrenzt | ⭐⭐⭐ **Zukunft** |

---

## 🛠️ Implementierungs-Roadmap

### **Woche 1: Foundation**
- [ ] Django API-Endpoint erstellen: `/api/quotes/create-draft/`
- [ ] n8n Workflow erweitern (nach Vollständigkeitsprüfung)
- [ ] OpenAI Prompt für Produktauswahl schreiben
- [ ] Test mit 5 echten Prechecks

### **Woche 2: Optimierung**
- [ ] Function Calling implementieren
- [ ] Validierungs-Logik in n8n
- [ ] E-Mail-Template für Team-Benachrichtigung
- [ ] Dashboard: Angebots-Entwurf-Ansicht

### **Woche 3: Testing**
- [ ] 20 Test-Angebote erstellen
- [ ] Feedback-Schleife mit Team
- [ ] Prompt-Optimierung basierend auf Feedback
- [ ] Fehlerbehandlung verbessern

### **Woche 4: Go-Live**
- [ ] Production-Deployment
- [ ] Monitoring einrichten
- [ ] Dokumentation für Team
- [ ] Training: Wie prüft man KI-Entwürfe?

### **Monat 2: Skalierung**
- [ ] RAG mit Vektordatenbank (optional)
- [ ] Mehr Wissensquellen einbinden
- [ ] Mehrsprachigkeit (EN/DE)
- [ ] Automatische Freigabe bei hoher Konfidenz (>95%)

---

## 📝 Beispiel: Wissensdatenbank-Struktur

**Datei:** `knowledge_base/products.json`

```json
{
  "inverters": [
    {
      "id": 70,
      "name": "Fronius Symo 8.2-3-M",
      "manufacturer": "Fronius",
      "power_kw": 8.2,
      "phases": 3,
      "price_net": 1500,
      "features": [
        "WLAN-Datenlogger integriert",
        "99.0% Wirkungsgrad",
        "IP65 Schutzklasse",
        "10 Jahre Garantie"
      ],
      "compatible_batteries": ["Fronius Solar Battery", "BYD HVM", "LG Chem RESU"],
      "best_for": {
        "building_types": ["efh", "mfh"],
        "power_range": [6, 10],
        "notes": "Ideal für Einfamilienhäuser mit 6-10 kWp Anlagengröße"
      },
      "installation_notes": [
        "Mindestens 30cm Abstand zu Wand",
        "Belüftung nach oben sicherstellen",
        "Kein direktes Sonnenlicht"
      ],
      "why_recommend": "Zuverlässiger Premium-Wechselrichter mit exzellentem Monitoring"
    }
  ],
  "installation_guidelines": {
    "cable_sizing": {
      "up_to_5kw": "6mm² NYM-J 3x1.5",
      "5_to_10kw": "10mm² NYM-J 5x2.5",
      "above_10kw": "16mm² NYM-J 5x4"
    },
    "surge_protection": {
      "required": true,
      "type": "Typ 2 AC-seitig",
      "coordination": "Mit vorhandenem SPD abstimmen"
    },
    "grid_connection": {
      "TN_network": {
        "required_fuse": "Mindestens 35A",
        "selective_protection": "Empfohlen ab 10kW"
      },
      "TT_network": {
        "additional_measures": "Zusätzlicher Erdungsstab erforderlich",
        "surcharge": 150
      }
    }
  },
  "offer_templates": {
    "efh_standard": {
      "intro": "Sehr geehrte/r {customer_name},\n\nvielen Dank für Ihr Interesse an einer PV-Anlage. Auf Basis Ihrer Angaben erstellen wir folgendes Angebot:",
      "closing": "Gerne beraten wir Sie persönlich zu den Details. Vereinbaren Sie einfach einen Termin unter {phone}.",
      "validity_days": 30
    }
  }
}
```

---

## 🎯 Zusammenfassung & Empfehlung

### **✅ MEINE EMPFEHLUNG:**

**Starte mit Option 2+3 (In-Prompt + Function Calling)**

**Warum?**
1. ✅ **Schnell** - In 1-2 Tagen einsatzbereit
2. ✅ **Günstig** - ~$3-30/Monat
3. ✅ **Flexibel** - Einfach anzupassen
4. ✅ **Sicher** - Manuelle Prüfung vor Versand
5. ✅ **Lernend** - Sammelt Daten für spätere Optimierung

**Dann später:** Upgrade zu RAG (Option 1) wenn:
- > 50 Angebote/Monat
- Mehr als 100 Produkte im Katalog
- Mehrere Wissensquellen (PDFs, Handbücher)
- Vollautomatisierung gewünscht

---

## 📚 Nächste Schritte

1. **Entscheidung:** Welche Option möchtest du implementieren?
2. **API-Endpoint:** Soll ich `/api/quotes/create-draft/` erstellen?
3. **n8n Workflow:** Soll ich den erweiterten Workflow schreiben?
4. **Prompt-Template:** Brauchst du ein konkretes OpenAI-Prompt-Beispiel?

---

**Erstellt:** 2025-11-20
**Version:** 1.0
**Status:** Strategieempfehlung - Bereit zur Umsetzung
