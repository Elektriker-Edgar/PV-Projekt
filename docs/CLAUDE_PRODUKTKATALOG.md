# CLAUDE_PRODUKTKATALOG.md - Produktkatalog-System Dokumentation

> Vollständige Dokumentation des Produktkatalog-Systems inkl. Bootstrap Delete-Modals

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)

---

## 📋 Übersicht

**Version:** 1.2.0 (2025-11-11)
**Status:** ✅ VOLLSTÄNDIG IMPLEMENTIERT & GETESTET
**Erstellt:**  2025-11-11

### Hauptfunktionen

- ✅ **Produktkategorien** - Verwaltung von 7 Kategorien
- ✅ **Produktkatalog** - 30+ Artikel mit EK/VK-Preisen
- ✅ **Automatische Kalkulation** - Brutto-Preise & Margen
- ✅ **Filter & Suche** - Kategorie, Status, SKU-Suche
- ✅ **Bootstrap Delete-Modals** - Professionelle Lösch-Bestätigungen
- ✅ **PROTECT on Delete** - Verhindert Löschen von Kategorien mit Produkten
- ✅ **Minimalistisches Design** - Kompakte, übersichtliche Tabellen

---

## 🗄️ Datenmodelle

### ProductCategory Model

**Datei:** `apps/quotes/models.py:273-297`

```python
class ProductCategory(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def get_product_count(self):
        return self.products.filter(is_active=True).count()
```

### Product Model

**Datei:** `apps/quotes/models.py:299-419`

```python
class Product(models.Model):
    # Basis
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)

    # Preise
    purchase_price_net = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price_net = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.19)

    # Lagerbestand (optional)
    stock_quantity = models.IntegerField(default=0, blank=True, null=True)
    min_stock_level = models.IntegerField(default=0, blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Zusatz
    manufacturer = models.CharField(max_length=200, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    @property
    def sales_price_gross(self):
        return self.sales_price_net * (1 + self.vat_rate)

    @property
    def margin_percentage(self):
        if self.purchase_price_net > 0:
            return ((self.sales_price_net - self.purchase_price_net) /
                    self.purchase_price_net) * 100
        return Decimal('0.00')
```

---

## 🔗 URL-Struktur

**Datei:** `apps/core/dashboard_urls.py`

| URL | View | Template |
|-----|------|----------|
| `/dashboard/catalog/categories/` | ProductCategoryListView | category_list.html |
| `/dashboard/catalog/categories/create/` | ProductCategoryCreateView | category_form.html |
| `/dashboard/catalog/categories/<id>/edit/` | ProductCategoryUpdateView | category_form.html |
| `/dashboard/catalog/categories/<id>/delete/` | ProductCategoryDeleteView | - |
| `/dashboard/catalog/products/` | ProductListView | product_list.html |
| `/dashboard/catalog/products/create/` | ProductCreateView | product_form.html |
| `/dashboard/catalog/products/<id>/edit/` | ProductUpdateView | product_form.html |
| `/dashboard/catalog/products/<id>/delete/` | ProductDeleteView | - |

---

## 📊 Views-Dokumentation

### ProductCategoryListView

**URL:** `/dashboard/catalog/categories/`
**Template:** `dashboard/category_list.html`

**Features:**
- Statistik-Cards (Gesamt, Aktiv, Inaktiv)
- Suche nach Kategoriename
- Inline-Modal zum schnellen Erstellen
- Product-Count pro Kategorie
- Delete-Modals mit PROTECT-Warnung

**Context:**
```python
{
    'categories': QuerySet[ProductCategory],
    'stats': {
        'total': 7,
        'active': 7,
        'inactive': 0
    }
}
```

### ProductListView

**URL:** `/dashboard/catalog/products/`
**Template:** `dashboard/product_list.html`

**Features:**
- 11-Spalten Tabelle (SKU, Name, Kategorie, Einheit, EK, VK netto, VK brutto, MwSt., Marge, Status, Aktionen)
- Filter: Suche, Kategorie, Status, Sortierung
- Automatische Brutto-Berechnung
- Farbcodierte Margen (Rot <0%, Gelb <20%, Grün ≥20%)
- Pagination (50/Seite)
- Checkboxen + Bulk-Aktionen (verschieben, kopieren, löschen) inkl. Sammellösch-Modal
- Filter persistieren per Session – Reloads behalten Kategorie/Sortierung bei

**Bulk-Bar Verhalten (neu in 2025‑11‑11):**
- Checkbox in Tabellenkopf markiert/entfernt alle Produkte.
- Buttons besitzen `data-bulk-action` Attribute (`move`, `copy`, `delete`) und senden das gemeinsame Formular `product-bulk-form`.
- Bei **Löschen** öffnet ein Bootstrap-Modal (`#bulkDeleteModal`) mit Warntext. Erst die Bestätigung feuert den POST auf `/dashboard/catalog/products/bulk-action/`.
- Kopieren erlaubt exakt **ein** markiertes Produkt; danach wird der Nutzer zu `/catalog/products/create/?copy_from=<id>` umgeleitet und das Formular ist mit allen Werten vorbefüllt.
- Delete-Modals

**Query-Parameter:**
```
?search=kabel&category=5&status=active&sort=sku
```

**Context:**
```python
{
    'products': QuerySet[Product],
    'categories': QuerySet[ProductCategory],
    'stats': {
        'total': 30,
        'active': 30,
        'featured': 0
    }
}
```

### ProductCreateView / ProductUpdateView

**Template:** `dashboard/product_form.html`

**5 Karten-Layout:**
1. **Grunddaten** - Name, SKU, Kategorie, Einheit, Beschreibung
2. **Preise & Kalkulation** - EK/VK, MwSt., Live-Berechnung
3. **Lagerbestand** - Bestand, Mindestbestand, Warnungen
4. **Lieferanten & Hersteller** - Hersteller, Lieferant, Notizen
5. **Status & Optionen** - Aktiv, Hervorgehoben, Metadaten

**Live-Kalkulation:**
```javascript
// Wird in Template berechnet:
Bruttopreis: {{ product.sales_price_gross|floatformat:2 }}€
Marge: {{ product.margin_amount|floatformat:2 }}€ ({{ product.margin_percentage|floatformat:1 }}%)
```

---

## 🎨 Bootstrap Delete-Modals

### Implementierung in Templates

**Precheck Delete Modal** (`dashboard/precheck_list.html:208-252`)

```html
<button type="button" class="btn btn-sm btn-danger"
        data-bs-toggle="modal"
        data-bs-target="#deleteModal{{ precheck.id }}">
    <i class="fas fa-trash"></i>
</button>

<div class="modal fade" id="deleteModal{{ precheck.id }}" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-danger text-white">
                <h5 class="modal-title">
                    <i class="fas fa-exclamation-triangle"></i> Precheck löschen
                </h5>
                <button type="button" class="btn-close btn-close-white"
                        data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p><strong>Möchten Sie Precheck #{{ precheck.id }} wirklich löschen?</strong></p>
                <div class="alert alert-warning">
                    <strong>Warnung:</strong> Diese Aktion kann nicht rückgängig gemacht werden!
                </div>
                <p><strong>Folgende Daten werden gelöscht:</strong></p>
                <ul>
                    <li>Precheck von <strong>{{ precheck.site.customer.name }}</strong></li>
                    {% if precheck.quote %}
                    <li>Verknüpftes Angebot und alle Positionen</li>
                    {% endif %}
                    <li>Alle hochgeladenen Fotos und Dateien</li>
                </ul>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary"
                        data-bs-dismiss="modal">
                    <i class="fas fa-times"></i> Abbrechen
                </button>
                <form method="post"
                      action="{% url 'dashboard:precheck_delete' pk=precheck.id %}"
                      style="display: inline;">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">
                        <i class="fas fa-trash"></i> Endgültig löschen
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
```

### Customer Delete Modal mit CASCADE-Warnung

**Datei:** `dashboard/customer_list.html:162-206`

```html
<div class="modal-body">
    <p><strong>Möchten Sie den Kunden "{{ customer.name }}" wirklich löschen?</strong></p>
    <div class="alert alert-danger">
        <i class="fas fa-exclamation-triangle"></i>
        <strong>ACHTUNG:</strong> Dies ist eine destruktive Operation!
    </div>
    <p><strong>Folgende Daten werden CASCADE gelöscht:</strong></p>
    <ul>
        <li><strong>{{ customer.sites.count }}</strong> Standort(e)</li>
        <li><strong>{{ customer.total_prechecks }}</strong> Precheck(s)</li>
        <li>Alle verknüpften Angebote</li>
        <li>Alle hochgeladenen Dateien</li>
    </ul>
    <p class="text-danger mt-3"><strong>Diese Aktion kann NICHT rückgängig gemacht werden!</strong></p>
</div>
```

### Product Delete Modal

**Datei:** `dashboard/product_list.html` (generiert per View)

```html
<div class="modal-body">
    <p><strong>Möchten Sie das Produkt "{{ product.name }}" ({{ product.sku }}) wirklich löschen?</strong></p>
    <div class="alert alert-warning">
        <strong>Warnung:</strong> Diese Aktion kann nicht rückgängig gemacht werden!
    </div>
</div>
```

### Category Delete Modal mit PROTECT-Warnung

**Datei:** `dashboard/category_list.html`

```html
<div class="modal-body">
    <p><strong>Möchten Sie die Kategorie "{{ category.name }}" wirklich löschen?</strong></p>
    {% if category.products.count > 0 %}
    <div class="alert alert-danger">
        <i class="fas fa-exclamation-triangle"></i>
        <strong>FEHLER:</strong> Diese Kategorie kann nicht gelöscht werden!
    </div>
    <p>Die Kategorie enthält noch <strong>{{ category.products.count }}</strong> Produkt(e).</p>
    <p>Löschen oder verschieben Sie zuerst alle Produkte.</p>
    {% else %}
    <div class="alert alert-warning">
        <strong>Warnung:</strong> Diese Aktion kann nicht rückgängig gemacht werden!
    </div>
    {% endif %}
</div>
```

---

## 📦 Test-Daten

**Script:** `create_test_products.py`

### Erstellte Kategorien & Produkte

| Kategorie | Produkte | Beispiele |
|-----------|----------|-----------|
| Precheck-Artikel | 6 | PRECHK-BASE, TRAVEL-0, TRAVEL-30 |
| Wechselrichter | 4 | INV-FRONIUS-5, INV-KOSTAL-8 |
| Speicher | 3 | BAT-BYD-5, BAT-VARTA-6 |
| Installationsmaterial | 4 | INST-SPD-T1T2, INST-AC-WIRE |
| Kabel | 4 | CABLE-DC-6MM, CABLE-AC-5G6 |
| Dienstleistungen | 5 | SVC-INSTALL-BASE, SVC-ELECTRICIAN |
| Zubehör | 4 | ACC-WALLBOX-11KW, ACC-MONITOR |

**Ausführen:**
```bash
python "E:\ANPR\PV-Service\venv\Scripts\python.exe" create_test_products.py
```

**Ausgabe:**
```
Erstelle Produktkategorien...
  [o] Existiert bereits: Precheck-Artikel
  [+] Erstellt: Wechselrichter
  ...

Erstelle Produkte...
  [+] PRECHK-BASE - Basis-Paket
  [+] INV-FRONIUS-5 - Fronius Symo 5.0-3-M
  ...

Kategorien: 7
Produkte: 30
```

---

## 🎨 Design & Styling

### Farbschema (Margen)

```css
/* Marge Farben */
.margin-negative { color: #ef4444; }  /* Rot: Negativ */
.margin-low      { color: #f59e0b; }  /* Orange: <20% */
.margin-good     { color: #10b981; }  /* Grün: ≥20% */
```

### Tabellen-Layout

**11 Spalten in product_list.html:**
1. SKU (code-Stil)
2. Bezeichnung (+ Hersteller wenn vorhanden)
3. Kategorie (Badge)
4. Einheit
5. EK (netto)
6. VK (netto)
7. VK (brutto) - automatisch berechnet
8. MwSt.
9. Marge % - farbcodiert
10. Status (Badge)
11. Aktionen (Edit/Delete)

**Kompakt & Übersichtlich:**
- Feste Spaltenbreiten
- Zentrierte Zahlen
- Icons für bessere Lesbarkeit
- Hover-Effekte

---

## 🔐 Sicherheitsfeatures

### 1. PROTECT on Delete

**Kategorie-Löschung verhindert:**
```python
category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT)
```

**Fehler wenn Produkte vorhanden:**
```
ProtectedError: Cannot delete category because it has products
```

### 2. CSRF-Protection

**Alle Delete-Forms:**
```html
<form method="post" action="...">
    {% csrf_token %}
    <button type="submit">Löschen</button>
</form>
```

### 3. LoginRequiredMixin

**Alle Views geschützt:**
```python
class ProductListView(LoginRequiredMixin, ListView):
    login_url = '/admin/login/'
```

```python
class ProductBulkActionView(LoginRequiredMixin, View):
    """
    POST /dashboard/catalog/products/bulk-action/
    Aktionen: delete | move | copy
    """
```

### 4. SKU-Validierung

**Form-Validierung:**
```python
def clean_sku(self):
    sku = self.cleaned_data['sku'].upper()
    # Nur Buchstaben, Zahlen, Bindestrich, Underscore
    if not re.match(r'^[A-Z0-9_-]+$', sku):
        raise ValidationError("SKU darf nur Buchstaben, Zahlen, - und _ enthalten")
    return sku
```

---

## 🔧 Häufige Aufgaben

### Produkt erstellen

```python
from apps.quotes.models import ProductCategory, Product
from decimal import Decimal

# Kategorie abrufen
category = ProductCategory.objects.get(name="Wechselrichter")

# Produkt erstellen
Product.objects.create(
    category=category,
    sku="INV-CUSTOM-10",
    name="Custom Wechselrichter 10kW",
    unit="piece",
    purchase_price_net=Decimal("1000.00"),
    sales_price_net=Decimal("1500.00"),
    vat_rate=Decimal("0.19"),
    stock_quantity=5,
    manufacturer="Custom Brand"
)
```

### Kategorie mit Produkten löschen

```python
# ❌ FALSCH - Fehler wegen PROTECT
category = ProductCategory.objects.get(id=2)
category.delete()  # → ProtectedError

# ✅ RICHTIG - Erst Produkte verschieben oder löschen
products = category.products.all()
new_category = ProductCategory.objects.get(name="Zubehör")

# Produkte verschieben
products.update(category=new_category)

# Dann Kategorie löschen
category.delete()
```

### Preise bulk-update

```python
from apps.quotes.models import Product
from decimal import Decimal

# Alle Wechselrichter 10% teurer machen
inverters = Product.objects.filter(category__name="Wechselrichter")
for inv in inverters:
    inv.sales_price_net = inv.sales_price_net * Decimal("1.10")
    inv.save()

# Oder mit update()
Product.objects.filter(category__name="Wechselrichter").update(
    sales_price_net=F('sales_price_net') * Decimal('1.10')
)
```

---

## 🐛 Troubleshooting

### Problem: "Kategorie kann nicht gelöscht werden"

**Ursache:** PROTECT on_delete verhindert Löschung

**Lösung:**
1. Produkte in andere Kategorie verschieben ODER
2. Produkte einzeln löschen
3. Dann Kategorie löschen

### Problem: SKU-Duplikat-Fehler

**Ursache:** SKU muss unique sein

**Lösung:**
```python
# Prüfen ob SKU existiert
if Product.objects.filter(sku="INV-TEST").exists():
    # SKU ändern oder anderes Produkt updaten
    pass
```

### Problem: Brutto-Preis wird nicht angezeigt

**Ursache:** Property wird im Template nicht als Methode aufgerufen

**Lösung:**
```html
<!-- ❌ FALSCH -->
{{ product.sales_price_gross() }}

<!-- ✅ RICHTIG -->
{{ product.sales_price_gross }}
```

---

## 📈 Performance-Tipps

### Query-Optimierung

```python
# ❌ SCHLECHT (N+1 Queries)
products = Product.objects.all()
for product in products:
    print(product.category.name)  # Extra Query!

# ✅ GUT (1 Query)
products = Product.objects.select_related('category')
for product in products:
    print(product.category.name)
```

### Aggregation

```python
# Statistiken effizient berechnen
from django.db.models import Count, Avg, Sum

stats = ProductCategory.objects.annotate(
    product_count=Count('products'),
    avg_price=Avg('products__sales_price_net'),
    total_stock=Sum('products__stock_quantity')
)
```

---

## Precheck-Bausteine (PCHK-SKUs)

Die vereinfachte Precheck-Kalkulation liest ausschliesslich Produkte mit der Struktur PCHK-<KEY>. Migration 
| SKU | Kategorie | Beschreibung |
|-----|-----------|--------------|
| PCHK-BUILDING-EFH/MFH/COMMERCIAL | Dienstleistung | Gebaeudeaufschlaege |
| PCHK-GRID-1P/3P | Dienstleistung | Zuschlag je Hausanschluss |
| PCHK-INVERTER-TIER-* | Produkte | WR-Staffeln (3/5/10/20/30 kW) |
| PCHK-STORAGE-TIER-* | Produkte | Speicherstaffeln (3/5/10 kWh) |
| PCHK-WR-CABLE-PM-LT* | Produkte | Preis pro Meter WR-Kabel |
| PCHK-WALLBOX-BASE-* | Produkte | Wallbox-Basiskosten (4/11/22 kW) |
| PCHK-WALLBOX-CABLE-PM-* | Produkte | Meterpreis Wallbox-Kabel |
| PCHK-WALLBOX-MOUNT-STAND, PCHK-WALLBOX-PV-SURPLUS | Dienstleistungen | Zusaetzliche Aufschlaege |

> **Pflegehinweis:** Werte bitte ausschliesslich ueber den Produktkatalog anpassen – die API uebernimmt diese Preise 1:1, Rabatte oder Pakete werden nicht mehr automatisch berechnet.

---

## 📚 Zusammenfassung der Änderungen

### Neue Dateien

```
E:\ANPR\PV-Service\
├── apps/quotes/models.py           [ERWEITERT] +147 Zeilen (ProductCategory, Product)
├── apps/core/dashboard_views.py    [ERWEITERT] +8 Views
├── apps/core/dashboard_urls.py     [ERWEITERT] +8 URLs
├── apps/core/forms.py             [ERWEITERT] ProductCategoryForm, ProductForm
├── templates/dashboard/
│   ├── category_list.html         [NEU] Kategorienliste
│   ├── category_form.html         [NEU] Kategorie bearbeiten
│   ├── product_list.html          [NEU] Produktliste (11 Spalten)
│   ├── product_form.html          [NEU] Produkt bearbeiten (5 Karten)
│   ├── base.html                  [ERWEITERT] Sidebar mit Produktkatalog
│   ├── precheck_list.html         [ERWEITERT] Bootstrap Delete-Modal
│   ├── precheck_detail.html       [ERWEITERT] Bootstrap Delete-Modal
│   ├── customer_list.html         [ERWEITERT] Bootstrap Delete-Modal + CASCADE-Warnung
│   └── customer_detail.html       [ERWEITERT] Bootstrap Delete-Modal + CASCADE-Warnung
├── create_test_products.py        [NEU] Test-Daten Script
└── docs/CLAUDE_PRODUKTKATALOG.md  [NEU] Diese Dokumentation
```

### Geänderte Dateien

```
apps/quotes/migrations/0010_productcategory_product.py  [NEU]
```

---

**Status:** ✅ VOLLSTÄNDIG IMPLEMENTIERT & GETESTET
**Letztes Update:** 2025-11-11
**Version:** 1.2.0

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)
