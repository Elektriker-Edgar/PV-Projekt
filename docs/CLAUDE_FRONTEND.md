# CLAUDE_FRONTEND.md - Frontend & JavaScript Dokumentation

> Detaillierte Dokumentation der Frontend-Implementierung, JavaScript-Funktionen und CSS-Struktur

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)

---

## 📄 HTML-Struktur: 6-Schritte Preisrechner

**Datei:** `templates/quotes/precheck_wizard.html`
**Zeilen:** ~845
**Framework:** Bootstrap 5.1.3

### Formular-Grundstruktur

```html
<form id="precheckWizard" method="post" enctype="multipart/form-data">
    {% csrf_token %}

    <!-- Progress-Bar (3 sichtbare Schritte) -->
    <div class="progress-container">
        <div class="progress-bar-wrapper">
            <div class="progress">
                <div id="mainProgress" class="progress-bar"></div>
            </div>
            <div class="progress-steps">
                <div class="progress-step active" data-visible-step="1">1</div>
                <div class="progress-step" data-visible-step="2">2</div>
                <div class="progress-step" data-visible-step="3">€</div>
            </div>
            <div class="progress-labels">
                <div class="progress-label active" data-visible-step="1">Standort & Elektro</div>
                <div class="progress-label" data-visible-step="2">PV-System</div>
                <div class="progress-label" data-visible-step="3">Preis</div>
            </div>
        </div>
    </div>

    <!-- Step Contents -->
    <div class="step-content active" data-step="1">...</div>
    <div class="step-content" data-step="2">...</div>
    <div class="step-content" data-step="3">...</div>
    <div class="step-content" data-step="4">...</div>
    <div class="step-content" data-step="5">...</div>
    <div class="step-content" data-step="6">...</div>
</form>
```

---

## 🔧 Schritt 1: Standort & Elektroinstallation

### Basis-Felder

```html
<div class="form-card step-content active" data-step="1">
    <h3><i class="fas fa-location-dot me-3"></i>Standort & Elektroinstallation</h3>

    <!-- Gebäudetyp -->
    <label for="building_type">Gebäudetyp *</label>
    <select id="building_type" name="building_type" required>
        <option value="">Bitte wählen...</option>
        <option value="single_family">Einfamilienhaus</option>
        <option value="multi_family">Mehrfamilienhaus</option>
        <option value="commercial">Gewerbe</option>
        <option value="apartment">Eigentumswohnung</option>
    </select>

    <!-- Baujahr -->
    <input type="number" id="construction_year" name="construction_year"
           min="1900" max="2025" placeholder="z.B. 1995" required>

    <!-- Sanierung (conditional) -->
    <input type="checkbox" id="has_renovation" onchange="toggleRenovationYear()">
    <label for="has_renovation">Elektrische Sanierung durchgeführt</label>

    <div id="renovationYearField" style="display:none">
        <input type="number" id="renovation_year" name="renovation_year"
               min="1900" max="2025" placeholder="z.B. 2015">
    </div>

    <!-- Hauptsicherung -->
    <input type="number" id="main_fuse_ampere" name="main_fuse_ampere"
           min="25" max="100" placeholder="z.B. 35" required>

    <!-- Netzart -->
    <select id="grid_type" name="grid_type" required>
        <option value="">Bitte wählen...</option>
        <option value="3p">3-Phasen (Standard)</option>
        <option value="1p">1-Phase</option>
        <option value="TT">TT-Netz</option>
    </select>

    <!-- Distanz Zähler→WR -->
    <input type="number" id="distance_meter_to_inverter" name="distance_meter_to_inverter"
           min="1" max="100" step="0.5" placeholder="z.B. 15" required>

    <!-- Montageorte (nebeneinander) -->
    <div class="row">
        <div class="col-md-6">
            <label for="inverter_location">Wechselrichter-Montageort *</label>
            <select id="inverter_location" name="inverter_location" required>
                <option value="">Bitte wählen...</option>
                <option value="basement">Keller</option>
                <option value="garage">Garage</option>
                <option value="attic">Dachboden</option>
                <option value="utility_room">Hauswirtschaftsraum</option>
                <option value="outdoor">Außenbereich</option>
                <option value="other">Anderer Ort</option>
            </select>
        </div>
        <div class="col-md-6">
            <label for="storage_location">Speicher-Montageort (optional)</label>
            <select id="storage_location" name="storage_location">
                <option value="">Kein Speicher / Später entscheiden</option>
                <option value="same_as_inverter">Wie Wechselrichter</option>
                <option value="basement">Keller</option>
                <option value="garage">Garage</option>
                <option value="attic">Dachboden</option>
                <option value="utility_room">Hauswirtschaftsraum</option>
                <option value="other">Anderer Ort</option>
            </select>
        </div>
    </div>

    <!-- Netzbetreiber -->
    <select id="grid_operator" name="grid_operator">
        <option value="">Optional - wird für Anmeldung benötigt</option>
        <option value="stromnetz_hamburg">Stromnetz Hamburg</option>
        <option value="sh_netz">SH Netz</option>
        <option value="eon_hanse">E.ON Hanse</option>
        <option value="other">Anderer Netzbetreiber</option>
    </select>

    <!-- Wallbox-Option (NEU) -->
    <div class="form-check">
        <input type="checkbox" id="has_wallbox" name="has_wallbox"
               class="form-check-input" onchange="toggleWallboxVisibility()">
        <label class="form-check-label" for="has_wallbox">
            <strong>Wallbox gewünscht?</strong> (wird in Schritt 2 konfiguriert)
        </label>
    </div>

    <!-- Navigation -->
    <div class="wizard-buttons">
        <button type="button" class="btn-secondary" onclick="prevStep()" disabled>
            <i class="fas fa-arrow-left me-2"></i>Zurück
        </button>
        <button type="button" class="btn-primary" onclick="nextStep()">
            Weiter<i class="fas fa-arrow-right ms-2"></i>
        </button>
    </div>
</div>
```

---

## ⚡ Schritt 2: PV-Wünsche & Wallbox-Details

```html
<div class="form-card step-content" data-step="2">
    <h3><i class="fas fa-solar-panel me-3"></i>PV-Wünsche & Konfiguration</h3>

    <!-- Gewünschte Leistung -->
    <input type="number" id="desired_power_kw" name="desired_power_kw"
           min="1" max="30" step="0.5" placeholder="z.B. 5" required>

    <!-- Speichergröße -->
    <input type="number" id="storage_kwh" name="storage_kwh"
           min="0" max="50" step="0.5" placeholder="z.B. 10 (0 = kein Speicher)">

    <!-- Wallbox-Felder (conditional, NEU) -->
    <div id="wallboxFields" style="display:none">
        <div class="wallbox-section">
            <h5><i class="fas fa-charging-station me-2"></i>Wallbox-Konfiguration</h5>

            <!-- Leistungsklasse -->
            <label for="wallbox_power">Wallbox Leistungsklasse *</label>
            <select id="wallbox_power" name="wallbox_power">
                <option value="4kw">&lt;4kW (Standard-Steckdose)</option>
                <option value="11kw" selected>11kW (Empfohlen)</option>
                <option value="22kw">22kW (Schnellladen)</option>
            </select>

            <!-- Montage -->
            <label for="wallbox_mount">Montage-Art *</label>
            <select id="wallbox_mount" name="wallbox_mount">
                <option value="wall" selected>Wandmontage</option>
                <option value="stand">Ständer (+ 350€)</option>
            </select>

            <!-- PV-Überschussladen -->
            <div class="form-check">
                <input type="checkbox" id="wallbox_pv_surplus" name="wallbox_pv_surplus"
                       class="form-check-input">
                <label class="form-check-label" for="wallbox_pv_surplus">
                    PV-Überschussladen (intelligente Laderegelung)
                </label>
            </div>

            <!-- Kabel -->
            <div class="form-check">
                <input type="checkbox" id="wallbox_cable_installed" name="wallbox_cable_installed"
                       class="form-check-input" onchange="toggleWallboxCableLength()">
                <label class="form-check-label" for="wallbox_cable_installed">
                    Kabel bereits verlegt
                </label>
            </div>

            <div id="wallboxCableLengthField">
                <label for="wallbox_cable_length">Kabellänge zu verlegen (m) *</label>
                <input type="number" id="wallbox_cable_length" name="wallbox_cable_length"
                       min="0" max="100" step="0.5" placeholder="z.B. 15">
            </div>
        </div>
    </div>

    <!-- Berechnen-Button -->
    <div class="calculate-button-container">
        <button type="button" class="btn-calculate" onclick="calculateAndShowPrice()">
            Preis berechnen
            <i class="fas fa-calculator ms-2"></i>
        </button>
    </div>

    <!-- Navigation -->
    <div class="wizard-buttons">
        <button type="button" class="btn-secondary" onclick="prevStep()">
            <i class="fas fa-arrow-left me-2"></i>Zurück
        </button>
    </div>
</div>
```

---

## 💰 Schritt 3: Preisanzeige

```html
<div class="form-card step-content" data-step="3">
    <h3><i class="fas fa-euro-sign me-3"></i>Ihr individueller Preis</h3>

    <!-- Hauptpreis -->
    <div class="price-display-card">
        <div class="price-label">Gesamtpreis inkl. MwSt.</div>
        <div class="price-amount" id="finalPriceDisplay">0€</div>
        <div class="price-package">
            <span id="packageBadge" class="badge bg-success">Basis-Paket</span>
        </div>
    </div>

    <!-- Breakdown -->
    <div class="price-breakdown">
        <h5>Kostenaufstellung:</h5>

        <div class="breakdown-item">
            <span><i class="fas fa-plug me-2"></i>Elektroinstallation Wechselrichter</span>
            <span id="breakdownInverter" class="breakdown-value">0€</span>
        </div>

        <!-- Speicher (conditional) -->
        <div class="breakdown-item" id="breakdownStorageRow" style="display:none">
            <span><i class="fas fa-battery-full me-2"></i>Speicherinstallation</span>
            <span id="breakdownStorage" class="breakdown-value">0€</span>
        </div>

        <!-- Wallbox (conditional, NEU) -->
        <div class="breakdown-item" id="breakdownWallboxRow" style="display:none">
            <span><i class="fas fa-charging-station me-2"></i>Wallbox & Installation</span>
            <span id="breakdownWallbox" class="breakdown-value">0€</span>
        </div>

        <div class="breakdown-item">
            <span><i class="fas fa-plus-circle me-2"></i>Zuschläge</span>
            <span id="breakdownSurcharges" class="breakdown-value">0€</span>
        </div>

        <div class="breakdown-item">
            <span><i class="fas fa-tools me-2"></i>Material</span>
            <span id="breakdownMaterial" class="breakdown-value">0€</span>
        </div>

        <!-- Rabatt (conditional) -->
        <div class="breakdown-item breakdown-discount" id="breakdownDiscountRow" style="display:none">
            <span><i class="fas fa-tag me-2"></i>Komplett-Kit Rabatt</span>
            <span id="breakdownDiscount" class="breakdown-value">-0€</span>
        </div>

        <div class="breakdown-item breakdown-total">
            <strong><i class="fas fa-calculator me-2"></i>Gesamtpreis</strong>
            <strong id="breakdownTotal" class="breakdown-value">0€</strong>
        </div>
    </div>

    <!-- Navigation -->
    <div class="wizard-buttons">
        <button type="button" class="btn-secondary" onclick="prevStep()">
            <i class="fas fa-arrow-left me-2"></i>Zurück
        </button>
        <button type="button" class="btn-primary" onclick="nextStep()">
            Weiter<i class="fas fa-arrow-right ms-2"></i>
        </button>
    </div>
</div>
```

---

## 📷 Schritt 4: Fotos & Material

```html
<div class="form-card step-content" data-step="4">
    <h3><i class="fas fa-camera me-3"></i>Fotos & Material</h3>

    <p class="help-text">Bitte laden Sie Fotos hoch (optional, aber hilfreich für genaue Kalkulation)</p>

    <!-- Zählerschrank -->
    <label for="meter_cabinet_photo">
        <i class="fas fa-box me-2"></i>Foto Zählerschrank
    </label>
    <input type="file" id="meter_cabinet_photo" name="meter_cabinet_photo"
           accept="image/*,.pdf" class="form-control">

    <!-- Hausanschlusskasten -->
    <label for="hak_photo">
        <i class="fas fa-plug me-2"></i>Foto Hausanschlusskasten (HAK)
    </label>
    <input type="file" id="hak_photo" name="hak_photo"
           accept="image/*,.pdf" class="form-control">

    <!-- Montageort -->
    <label for="location_photo">
        <i class="fas fa-location-dot me-2"></i>Foto geplanter Montageort
    </label>
    <input type="file" id="location_photo" name="location_photo"
           accept="image/*,.pdf" class="form-control">

    <!-- Kabelweg -->
    <label for="cable_route_photo">
        <i class="fas fa-route me-2"></i>Foto geplanter Kabelweg
    </label>
    <input type="file" id="cable_route_photo" name="cable_route_photo"
           accept="image/*,.pdf" class="form-control">

    <!-- Eigenes Material -->
    <label for="own_material_description">Eigenes Material (optional)</label>
    <textarea id="own_material_description" name="own_material_description"
              rows="3" placeholder="Falls Sie eigene Komponenten mitbringen..."></textarea>

    <!-- Navigation -->
    <div class="wizard-buttons">
        <button type="button" class="btn-secondary" onclick="prevStep()">
            <i class="fas fa-arrow-left me-2"></i>Zurück
        </button>
        <button type="button" class="btn-primary" onclick="nextStep()">
            Weiter<i class="fas fa-arrow-right ms-2"></i>
        </button>
    </div>
</div>
```

---

## 👤 Schritt 5: Kontakt & Zusammenfassung

### Kontaktdaten

```html
<div class="form-card step-content" data-step="5">
    <h3><i class="fas fa-user me-3"></i>Kontakt & Zusammenfassung</h3>

    <!-- Name -->
    <input type="text" id="customer_name" name="customer_name"
           placeholder="Max Mustermann" required>

    <!-- E-Mail -->
    <input type="email" id="customer_email" name="customer_email"
           placeholder="max@beispiel.de" required>

    <!-- Telefon -->
    <input type="tel" id="customer_phone" name="customer_phone"
           placeholder="+49 40 12345678" required>

    <!-- Kundentyp -->
    <select id="customer_type" name="customer_type" required>
        <option value="">Bitte wählen...</option>
        <option value="private">Privatkunde</option>
        <option value="business">Geschäftskunde</option>
    </select>

    <!-- Adresse -->
    <input type="text" id="site_address" name="site_address"
           placeholder="Musterstraße 123, 20095 Hamburg" required>

    <!-- Eigene Komponenten -->
    <div class="form-check">
        <input type="checkbox" id="own_components" name="own_components"
               class="form-check-input">
        <label class="form-check-label" for="own_components">
            Ich bringe eigene Komponenten mit (WR/Speicher)
        </label>
    </div>

    <!-- Notizen -->
    <label for="notes">Anmerkungen (optional)</label>
    <textarea id="notes" name="notes" rows="3"
              placeholder="Weitere Informationen..."></textarea>
</div>
```

### Zusammenfassung (NEU mit Wallbox)

```html
<!-- Zusammenfassung -->
<div class="summary-card">
    <h5><i class="fas fa-list-check me-2"></i>Ihre Angaben</h5>

    <!-- Standort & Elektro -->
    <div class="summary-section">
        <h6>Standort & Elektro</h6>
        <div class="summary-item">
            <span>Gebäudetyp</span>
            <strong id="sum_building_type">-</strong>
        </div>
        <div class="summary-item">
            <span>Baujahr</span>
            <strong id="sum_construction_year">-</strong>
        </div>
        <div class="summary-item" id="sum_renovation_row" style="display:none">
            <span>Sanierung</span>
            <strong id="sum_renovation_year">-</strong>
        </div>
        <div class="summary-item">
            <span>Hauptsicherung</span>
            <strong id="sum_main_fuse">-</strong>
        </div>
        <div class="summary-item">
            <span>Netzart</span>
            <strong id="sum_grid_type">-</strong>
        </div>
        <div class="summary-item">
            <span>Distanz Zähler→WR</span>
            <strong id="sum_distance">-</strong>
        </div>
        <div class="summary-item">
            <span>WR-Montageort</span>
            <strong id="sum_inverter_loc">-</strong>
        </div>
        <div class="summary-item" id="sum_storage_loc_row" style="display:none">
            <span>Speicher-Montageort</span>
            <strong id="sum_storage_loc">-</strong>
        </div>
    </div>

    <!-- PV-System -->
    <div class="summary-section">
        <h6>PV-System</h6>
        <div class="summary-item">
            <span>Wechselrichter</span>
            <strong id="sum_wr_power">-</strong>
        </div>
        <div class="summary-item" id="sum_storage_row" style="display:none">
            <span>Speicher</span>
            <strong id="sum_storage">-</strong>
        </div>
        <div class="summary-item" id="sum_own_comp_row" style="display:none">
            <span>Eigene Komponenten</span>
            <strong>Ja</strong>
        </div>
    </div>

    <!-- Wallbox (NEU) -->
    <div class="summary-section" id="sum_wallbox_section" style="display:none">
        <h6>Wallbox</h6>
        <div class="summary-item">
            <span>Leistungsklasse</span>
            <strong id="sum_wb_power">-</strong>
        </div>
        <div class="summary-item">
            <span>Montage</span>
            <strong id="sum_wb_mount">-</strong>
        </div>
        <div class="summary-item" id="sum_wb_pv_row" style="display:none">
            <span>PV-Überschussladen</span>
            <strong>Ja</strong>
        </div>
        <div class="summary-item">
            <span>Kabelverlegung</span>
            <strong id="sum_wb_cable">-</strong>
        </div>
    </div>

    <!-- Preis -->
    <div class="summary-section">
        <h6>Preis</h6>
        <div class="summary-item">
            <strong>Gesamtpreis inkl. MwSt.</strong>
            <strong id="sum_total_price" class="text-success">0€</strong>
        </div>
    </div>
</div>
```

---

## ✅ Schritt 6: Datenschutz & Abschluss

```html
<div class="form-card step-content" data-step="6">
    <h3><i class="fas fa-shield-halved me-3"></i>Datenschutz & Abschluss</h3>

    <div class="consent-box">
        <div class="form-check">
            <input type="checkbox" id="consent" name="consent"
                   class="form-check-input" required>
            <label class="form-check-label" for="consent">
                Ich stimme der Verarbeitung meiner Daten gemäß der
                <a href="/datenschutz/" target="_blank">Datenschutzerklärung</a> zu. *
            </label>
        </div>
    </div>

    <div class="wizard-buttons">
        <button type="button" class="btn-secondary" onclick="prevStep()">
            <i class="fas fa-arrow-left me-2"></i>Zurück
        </button>
        <button type="submit" class="btn-submit">
            <i class="fas fa-paper-plane me-2"></i>Angebot anfordern
        </button>
    </div>
</div>
```

---

## 🟢 JavaScript-Funktionen (Vollständig dokumentiert)

### Globale Variablen

```javascript
let currentStep = 1;        // Aktueller Schritt (1-6)
const totalSteps = 6;       // Gesamtanzahl Schritte
let priceData = null;       // Gespeicherte API-Response
```

### Navigation-Funktionen

#### nextStep()
```javascript
function nextStep() {
    if(!validateCurrentStep()) return;

    if(currentStep < totalSteps) {
        document.querySelector(`.step-content[data-step="${currentStep}"]`)
            .classList.remove('active');
        currentStep++;
        document.querySelector(`.step-content[data-step="${currentStep}"]`)
            .classList.add('active');

        // Zusammenfassung befüllen (WICHTIG: Nach dem Wechsel!)
        if(currentStep === 5) updateSummary();

        updateProgress();
        window.scrollTo({top: 0, behavior: 'smooth'});
        saveFormData();
    }
}
```

#### prevStep()
```javascript
function prevStep() {
    if(currentStep > 1) {
        document.querySelector(`.step-content[data-step="${currentStep}"]`)
            .classList.remove('active');
        currentStep--;
        document.querySelector(`.step-content[data-step="${currentStep}"]`)
            .classList.add('active');

        if(currentStep === 5) updateSummary();

        updateProgress();
        window.scrollTo({top: 0, behavior: 'smooth'});
    }
}
```

#### updateProgress() - 3-Punkte Progress-Bar
```javascript
function updateProgress() {
    let progressPercent = 0;
    let activeVisibleStep = 1;

    // Mapping: Steps 1-6 → Visible Steps 1-3
    if(currentStep === 1) {
        progressPercent = 0;
        activeVisibleStep = 1;       // Standort & Elektro
    } else if(currentStep === 2) {
        progressPercent = 50;
        activeVisibleStep = 2;       // PV-System
    } else if(currentStep >= 3) {
        progressPercent = 100;
        activeVisibleStep = 3;       // Preis
    }

    // Progress-Fill aktualisieren
    document.getElementById('mainProgress').style.width = progressPercent + '%';

    // Steps & Labels aktualisieren
    document.querySelectorAll('.progress-step').forEach((step, index) => {
        const visibleStepNum = index + 1;
        step.classList.remove('active', 'completed');
        if(visibleStepNum < activeVisibleStep)
            step.classList.add('completed');
        else if(visibleStepNum === activeVisibleStep)
            step.classList.add('active');
    });

    document.querySelectorAll('.step-label').forEach((label, index) => {
        const visibleStepNum = index + 1;
        label.classList.remove('active', 'completed');
        if(visibleStepNum < activeVisibleStep)
            label.classList.add('completed');
        else if(visibleStepNum === activeVisibleStep)
            label.classList.add('active');
    });
}
```

→ Fortsetzung in nächster Section...

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)
**Siehe auch:** [CLAUDE_API.md](CLAUDE_API.md) - API & Backend
