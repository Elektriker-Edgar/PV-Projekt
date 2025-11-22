du bist ein teil eines entwicklerteams für online projekte. du bist ein teil des experten-teams. 
Deine sprache ist deutsch. 
Aktuell arbeiten wir an einem Django Projekt für Online präsenz eines Elektrounternehmens. Informiere dich über Projektstand ud der Doku im Verzeichnss /docs/CLAUDE.md
Folgende Aufgabe wird aktuell bearbeitet: es soll automatische Kundenabwicklung mit Einbezug eines KI im n8n durchführt werden.
Der Kunde gibt in die Eingabefelder auf der Seite seine Gegebenheiten zu seinem Projekt. Die daten werden in der Datenbank gespeichert.
folgende Kundendaten werden über Webhook an n8n übertragen:
[
  {
    "headers": {
      "host": "localhost:5678",
      "user-agent": "python-requests/2.32.4",
      "accept-encoding": "gzip, deflate, br",
      "accept": "*/*",
      "connection": "keep-alive",
      "content-type": "application/json",
      "x-api-key": "",
      "content-length": "382"
    },
    "params": {},
    "query": {},
    "body": {
      "event": "precheck_submitted",
      "precheck_id": 64,
      "test_mode": true,
      "api_base_url": "http://192.168.178.30:8025",
      "api_endpoints": {
        "precheck_data": "/api/integrations/precheck/64/",
        "pricing_data": "/api/integrations/pricing/"
      },
      "metadata": {
        "customer_email": "hallo.elektriker@gmail.com",
        "has_customer": true,
        "has_site": true,
        "timestamp": "2025-11-20T01:42:02.360865+00:00"
      }
    },
    "webhookUrl": "http://localhost:5678/webhook-test/precheck-submitted",
    "executionMode": "test"
  }
]
Der N8n holt sich kundendaten mit dem API  "precheck_data": "/api/integrations/precheck/64/",
die daten sehen so aus:
[
  {
    "precheck_id": 59,
    "customer": {
      "id": 60,
      "name": "Max Mustermann Test",
      "email": "max.mustermann.test@example.com",
      "phone": "+49 40 12345678"
    },
    "site": {
      "id": 59,
      "address": "Teststraße 123\r\n20095 Hamburg",
      "building_type": {
        "value": "efh",
        "display": "Einfamilienhaus"
      },
      "main_fuse_ampere": 63,
      "grid_type": {
        "value": "3p",
        "display": "3-Polig"
      },
      "distance_meter_to_hak": 12.5,
      "has_photos": true,
      "photo_count": 4,
      "photos": [
        {
          "id": 61,
          "category": "cable_route",
          "category_display": "Kabelwege",
          "url": "http://192.168.178.30:8025/media/precheck/photos/2025/11/%C3%9Cbersicht_PV_lUsRnOf.pdf"
        },
        {
          "id": 59,
          "category": "hak",
          "category_display": "Hausanschlusskasten",
          "url": "http://192.168.178.30:8025/media/precheck/photos/2025/11/Stromz%C3%A4hler_UEYwJ9J.JPG"
        },
        {
          "id": 60,
          "category": "location",
          "category_display": "Montageorte",
          "url": "http://192.168.178.30:8025/media/precheck/photos/2025/11/Stromz%C3%A4hler_6wHSjTl.JPG"
        },
        {
          "id": 58,
          "category": "meter_cabinet",
          "category_display": "Zählerschrank",
          "url": "http://192.168.178.30:8025/media/precheck/photos/2025/11/Z%C3%A4hlerkasten_lKmvaJz.JPG"
        }
      ]
    },
    "project": {
      "desired_power_kw": 8.5,
      "storage_kwh": 10,
      "has_storage": true,
      "has_wallbox": true,
      "wallbox_class": {
        "value": "11kw",
        "display": "Wallbox 11 kW"
      },
      "wallbox_mount": {
        "value": "wall",
        "display": "Wandmontage"
      },
      "wallbox_cable_length": 25,
      "wallbox_cable_prepared": false,
      "wallbox_pv_surplus": true,
      "own_components": false,
      "own_material_description": "",
      "distance_meter_to_inverter": 12.5,
      "inverter_location": {
        "value": "basement",
        "display": "Keller"
      },
      "storage_location": {
        "value": "same_as_inverter",
        "display": "Gleicher Ort wie Wechselrichter"
      },
      "building_type": {
        "value": "efh",
        "display": "Einfamilienhaus"
      },
      "feed_in_mode": {
        "value": "surplus",
        "display": "Ueberschusseinspeisung"
      },
      "requires_backup_power": true,
      "has_heat_pump": true,
      "grid_operator": "hamburgnetze",
      "has_grounding": {
        "value": "yes",
        "display": "Ja, vorhanden"
      },
      "has_deep_earth": {
        "value": "yes",
        "display": "Ja, vorhanden"
      },
      "customer_notes": "Ich möchte gerne einen Fronius Wechselrichter haben. können Sie das anbieten. ich Würde bevorzügen einen vor ort termin zu vereinbaren."
    },
    "pricing": {
      "building_surcharge": 0,
      "grid_surcharge": 0,
      "inverter_price": 1500,
      "storage_price": 2000,
      "wr_cable_cost": 62.5,
      "wallbox_base_price": 500,
      "wallbox_cable_cost": 350,
      "wallbox_extra_cost": 200,
      "net_total": 4612.5,
      "vat_amount": 876.38,
      "gross_total": 5488.88
    },
    "completeness": {
      "has_customer_data": true,
      "has_customer_email": true,
      "has_customer_phone": true,
      "has_site_data": true,
      "has_site_address": true,
      "has_main_fuse": true,
      "has_grid_type": true,
      "has_photos": true,
      "has_meter_photo": true,
      "has_hak_photo": true,
      "has_power_data": true,
      "has_pricing": true,
      "has_inverter_location": true,
      "has_distance_data": true
    },
    "metadata": {
      "created_at": "2025-11-16T17:34:53.014342+00:00",
      "updated_at": "2025-11-16T17:34:53.023318+00:00",
      "has_quote": true,
      "quote_status": "review",
      "package_choice": null,
      "is_express_package": false
    }
  }
]
in N8n Sollen gleich mehrere KI Agenten welche sich auf bestimmte Aufgaben spezialisieren tätig sein.
Der Erste Ki-Agent ist ein Experte auf dem Bereich Elektroinstallation und ist als Arbeitsvorbereiter tätig.
Er soll bewerten ob die daten plausibel sind und ob alle daten vorhanden sind.
Ki soll nachsehen ob der Zählerschrank alt und erneuert werden muss, oder die Zähleranlage schon modernisiert wurde. können eventuell probleme bei der insalltation auftretten. Es soll mit eine zusammenfassung des daten zusammen stellen.

es soll für weitere verwendung von weiteren KI Agenten gut verständlich sein. JSON ist hier vorteilhaft.\    
es soll später  an weiteres n8n Workflow weitergegeben werden\
es gibt schon das webhook und das node zum abholen der daten von der django API. es soll ein netzwerk der agenten werden. geplannt ein Angebotersteller, Agent für Korrespondenz mit dem kunden und mir. \
die fotos sollen ebenfalls ausgewertet werden. das soll aber erst später implementiert werden.
