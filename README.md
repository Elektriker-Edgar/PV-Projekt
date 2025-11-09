# EDGARD Elektro - PV-Service Platform

**Django-basierte Website für PV-Anlagen Elektroinstallationsservice in Hamburg**

## 🚀 Quick Start

```bash
# Server starten
python manage.py runserver 192.168.178.30:8025

# Preisrechner öffnen
http://192.168.178.30:8025/precheck/
```

## 📚 Dokumentation

Die vollständige Projektdokumentation befindet sich im `/Docs` Verzeichnis:

- **[Docs/CLAUDE.md](Docs/CLAUDE.md)** - 📋 Hauptdokumentation mit Übersicht & Quick-Reference
- **[Docs/CLAUDE_API.md](Docs/CLAUDE_API.md)** - 🔌 API-Endpoints & Preisberechnung-Logik
- **[Docs/CLAUDE_FRONTEND.md](Docs/CLAUDE_FRONTEND.md)** - 🎨 Frontend, JavaScript & CSS
- **[Docs/CLAUDE_DATABASE.md](Docs/CLAUDE_DATABASE.md)** - 🗄️ Datenbank-Modelle & Migrationen
- **[Docs/CLAUDE_DEPLOYMENT.md](Docs/CLAUDE_DEPLOYMENT.md)** - 🚀 Deployment, Testing & Known Issues

## 🎯 Kern-Features

- ✅ **6-Schritte Preisrechner** mit Live-Preisberechnung
- ✅ **Wallbox-Integration** (4kW, 11kW, 22kW)
- ✅ **Variable Kabelpreise** abhängig von Leistungsklasse
- ✅ **Database-Driven Pricing** (25 PriceConfig-Einträge)
- ✅ **Enter-Taste Navigation** zwischen Feldern
- ✅ **3-Punkte Progress-Bar** (Standort → PV-System → Preis)
- ✅ **LocalStorage Persistierung**

## 📊 Projekt-Status

**Version:** 1.1.0 (2025-01-08)
**Status:** ✅ VOLL FUNKTIONSFÄHIG + WALLBOX-INTEGRATION

## 🔧 Wichtigste Befehle

```bash
# Migrationen
python manage.py makemigrations
python manage.py migrate

# Django Admin
python manage.py createsuperuser

# Django Shell
python manage.py shell
```

## 📝 Für KI-Agenten

Bitte lesen Sie **[Docs/CLAUDE.md](Docs/CLAUDE.md)** für:
- Projekt-Typ & Architektur
- Wichtigste Dateien & Code-Struktur
- Preisberechnung-Logik
- Anleitung zum Erweitern der Features

---

**Entwickelt mit:** Django 4.2 + Django REST Framework + Bootstrap 5
