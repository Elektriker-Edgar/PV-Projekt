# Precheck Test-Suite

Automatisierte Tests für den EDGARD Elektro Precheck-Wizard.

## 📁 Struktur

```
TESTS/
├── README.md                      # Diese Datei
├── test_precheck_automated.py     # Browser-Test (Playwright)
├── test_precheck_django.py        # Django-Test (ohne Browser)
├── run_tests.bat                  # Windows Batch-Script zum Ausführen
└── Bilder/                        # Vorhandene Test-Dateien
    ├── Zählerkasten.JPG
    ├── Stromzähler.JPG
    └── Übersicht_PV.pdf
```

---

## 🚀 Quick Start

### 1. Test-Bilder sind bereits vorhanden! ✅

Die vorhandenen Bilder in `TESTS/Bilder/` werden automatisch verwendet:
- `Zählerkasten.JPG` → für meter_cabinet_photo
- `Stromzähler.JPG` → für hak_photo und location_photo
- `Übersicht_PV.pdf` → für cable_route_photo

### 2. Playwright installieren (für Browser-Tests)

```bash
pip install playwright
playwright install chromium
```

### 3. Tests ausführen

**Einfachste Methode (Windows):**
```bash
cd E:\ANPR\PV-Service\TESTS
run_tests.bat
```

**Oder manuell:**

#### Browser-Test (empfohlen für End-to-End Testing)
```bash
cd E:\ANPR\PV-Service\TESTS
python test_precheck_automated.py
```

**Optionen:**
```bash
# Mit sichtbarem Browser (zum Debuggen)
python test_precheck_automated.py

# Im Hintergrund (schneller)
python test_precheck_automated.py --headless

# Schneller Modus (keine Verzögerungen)
python test_precheck_automated.py --fast

# Kombination
python test_precheck_automated.py --headless --fast
```

#### Django-Test (schneller, kein JavaScript)
```bash
cd E:\ANPR\PV-Service
python manage.py test TESTS.test_precheck_django

# Oder direkt:
python TESTS\test_precheck_django.py
```

---

## 📋 Was wird getestet?

### Browser-Test (`test_precheck_automated.py`)

✅ Vollständiger User-Flow:
- Alle 6 Schritte des Wizards
- Accordion-Navigation
- Dynamische Felder (Toggle-Funktionen)
- Datei-Uploads (JPG + PDF)
- LocalStorage-Persistierung
- API-Preisberechnung
- Formular-Submission
- Success-Seite

✅ Screenshots werden erstellt:
- `screenshot_preis_YYYYMMDD_HHMMSS.png`
- `screenshot_zusammenfassung_YYYYMMDD_HHMMSS.png`
- `screenshot_success_YYYYMMDD_HHMMSS.png`
- `screenshot_error_YYYYMMDD_HHMMSS.png` (bei Fehlern)

### Django-Test (`test_precheck_django.py`)

✅ Backend-Funktionalität:
- Formular-Validierung
- Datenbank-Operationen
- Model-Erstellung (Customer, Site, Precheck)
- Feld-Speicherung (alle 23 neuen Felder)
- Minimales Formular (nur Pflichtfelder)
- Vollständiges Formular (alle Felder)

---

## 🧪 Test-Daten

Die Tests verwenden folgende Standard-Daten:

### Kundendaten
- Name: Max Mustermann Test / Django Test User
- E-Mail: max.mustermann.test@example.com
- Telefon: +49 40 12345678
- Adresse: Teststraße 123, 20095 Hamburg

### PV-System
- Wechselrichter: 8.5 kW / 10.0 kW
- Speicher: 10.0 kWh / 12.0 kWh
- Wallbox: 11 kW mit PV-Überschussladen
- Wärmepumpe: Viessmann Vitocal 200-S, 8 kW

### Elektrische Daten
- Hauptsicherung: 63 A
- Hausanschluss: 3-Polig
- SLS-Schalter: Vorhanden
- Überspannungsschutz AC/DC: Vorhanden
- Kabelweg: 12.5 m / 15.0 m

---

## 🔧 Troubleshooting

### Problem: `FileNotFoundError` bei Test-Bildern

**Lösung:**
```bash
python TESTS\create_test_images.py
```

### Problem: Playwright-Fehler "Browser not found"

**Lösung:**
```bash
playwright install chromium
```

### Problem: Django-Test findet Module nicht

**Lösung:**
```bash
# Stelle sicher, dass du im Projekt-Root bist
cd E:\ANPR\PV-Service
python manage.py test TESTS.test_precheck_django
```

### Problem: "Server antwortet nicht"

**Lösung:**
```bash
# Starte den Development Server
python manage.py runserver 192.168.178.30:8025
```

### Problem: Test schlägt wegen fehlender Felder fehl

**Lösung:**
- Prüfe ob Migration 0018 angewendet wurde:
  ```bash
  python manage.py showmigrations quotes
  ```
- Falls nicht:
  ```bash
  python manage.py migrate quotes
  ```

---

## 📊 Test-Reports

### Browser-Test Output
```
==================================================
🚀 Starte automatisierten Precheck-Test
==================================================

🔍 Prüfe Test-Dateien in: E:\ANPR\PV-Service\TESTS\Bilder
   ✅ zaehler.jpg (0.45 MB)
   ✅ hausanschluss.jpg (0.38 MB)
   ✅ montageort.jpg (0.52 MB)
   ✅ kabelwege.pdf (0.12 MB)

🌐 Starte Browser (headless=False)...

📍 Öffne Precheck-Seite: http://192.168.178.30:8025/precheck/
✏️  SCHRITT 1: Standort & Elektro
   📦 Gebäude & Bauzustand
   ⚡ Elektrische Installation
   📍 Montageorte & Kabelwege
   ➡️  Weiter zu Schritt 2

✏️  SCHRITT 2: PV-Wünsche
   ☀️  PV-Konfiguration
   🔌 Zusatzgeräte (Wallbox & Wärmepumpe)
   💰 Preis berechnen...

✏️  SCHRITT 3: Preisanzeige
   ✅ Preis erfolgreich berechnet
   📸 Screenshot gespeichert: screenshot_preis_20250113_142530.png
   ➡️  Weiter zu Schritt 4

✏️  SCHRITT 4: Fotos hochladen
   📤 Upload zaehler.jpg...
   📤 Upload hausanschluss.jpg...
   📤 Upload montageort.jpg...
   📤 Upload kabelwege.pdf...
   ➡️  Weiter zu Schritt 5

✏️  SCHRITT 5: Kontaktdaten & Zusammenfassung
   📸 Screenshot gespeichert: screenshot_zusammenfassung_20250113_142535.png
   ➡️  Weiter zu Schritt 6

✏️  SCHRITT 6: Datenschutz & Absenden
   📨 Formular absenden...
   ⏳ Warte auf Erfolgsseite...

✅ SUCCESS-SEITE ERREICHT!
   📸 Screenshot gespeichert: screenshot_success_20250113_142538.png
   ✅ Angebot wurde erstellt

==================================================
🎉 TEST ERFOLGREICH ABGESCHLOSSEN!
==================================================
```

### Django-Test Output
```
🧪 Test: Vollständiges Precheck-Formular
==================================================

📤 Sende Precheck-Formular...
   Status Code: 200
   ✅ Prechecks erstellt: 1
   ✅ Customers erstellt: 1
   ✅ Sites erstellt: 1

📋 Erstellte Objekte:
   Customer: Django Test User (django.test@example.com)
   Site: Django-Teststraße 456
20095 Hamburg
   Precheck-ID: 1

✅ Alle Assertions erfolgreich!
==================================================
```

---

## 🎯 Best Practices

1. **Vor jedem Release:** Browser-Test einmal komplett durchlaufen lassen
2. **Während der Entwicklung:** Django-Tests für schnelles Feedback
3. **CI/CD Pipeline:** Beide Tests in `--headless` und `--fast` Modus
4. **Debugging:** Browser-Test ohne `--headless` zum Anschauen
5. **Screenshots:** Regelmäßig prüfen für visuelle Regression-Tests

---

## 📝 Nächste Schritte

- [ ] CI/CD Integration (GitHub Actions / Jenkins)
- [ ] Performance-Tests (Load Testing)
- [ ] Accessibility-Tests (WCAG 2.1)
- [ ] Cross-Browser-Tests (Firefox, Safari)
- [ ] Mobile-Responsive Tests
- [ ] API-Tests für `/api/pricing/preview/`

---

## 🤝 Contributing

Neue Tests hinzufügen:
1. Erstelle neue Testklasse in `test_precheck_django.py`
2. Oder neues Szenario in `test_precheck_automated.py`
3. Dokumentiere in dieser README
4. Führe alle Tests aus vor Commit

---

**Version:** 1.0.0
**Letzte Aktualisierung:** 2025-01-13
**Autor:** Claude Code Assistant
