# CLAUDE_QUOTE_EDITING.md - Angebots-Bearbeitung

> Detaillierte Dokumentation der Angebots-Bearbeitungsfunktionalität

**Zurück zur Hauptdokumentation:** [CLAUDE.md](CLAUDE.md)

**Erstellt:** 2025-01-16
**Version:** 1.3.0

---

## 📋 Übersicht

Das Angebots-Bearbeitungssystem ermöglicht es, automatisch generierte Angebote nachträglich anzupassen. Dies ist notwendig, wenn Kunden:
- Spezielle Wünsche äußern, die im Precheck nicht erfasst wurden
- Eigenes Material liefern (z.B. "BYD 19kW Speicher")
- Individuelle Positionen hinzufügen oder anpassen möchten

### Hauptfunktionen
- ✅ Positionen bearbeiten, hinzufügen und löschen
- ✅ Individuelle MwSt.-Sätze pro Position
- ✅ Produktkatalog-Autocomplete mit Tastatursteuerung
- ✅ Echtzeit-Berechnung aller Summen
- ✅ Split-MwSt.-Anzeige bei unterschiedlichen Sätzen
- ✅ Automatische Positionsnummerierung
- ✅ Notizfeld für Kundenwünsche

---

## 🏗️ Architektur

### Komponenten

| Komponente | Datei | Beschreibung |
|------------|-------|--------------|
| **Models** | `apps/quotes/models.py` | Quote, QuoteItem mit vat_rate |
| **Forms** | `apps/core/forms.py` | QuoteEditForm, QuoteItemForm, QuoteItemFormSet |
| **Views** | `apps/core/dashboard_views.py` | QuoteEditView, ProductAutocompleteView |
| **Templates** | `templates/dashboard/quote_edit.html` | Bearbeitungs-UI mit JavaScript |
| **URLs** | `apps/core/dashboard_urls.py` | `/quotes/<pk>/edit/` |

### Datenfluss

```
1. User klickt "Bearbeiten" → QuoteEditView (GET)
2. View lädt Quote + QuoteItemFormSet
3. Template rendert Formular mit JavaScript
4. User ändert Daten → JavaScript berechnet Summen live
5. User speichert → QuoteEditView (POST)
6. View validiert & speichert Quote + Items
7. Quote.save() triggert automatische Summenberechnung
8. Redirect zu quote_detail
```

---

## 📊 Datenbank-Änderungen

### Migration 0022: Quote.notes

**Datei:** `apps/quotes/migrations/0022_add_quote_notes.py`

```python
operations = [
    migrations.AddField(
        model_name='quote',
        name='notes',
        field=models.TextField(
            blank=True,
            help_text='Interne Notizen zu Sonderwünschen oder Anpassungen'
        ),
    ),
]
```

**Zweck:** Erfassung von Kundenwünschen und Anpassungsgründen

### Migration 0023: QuoteItem.vat_rate

**Datei:** `apps/quotes/migrations/0023_add_quoteitem_vat_rate.py`

```python
operations = [
    migrations.AddField(
        model_name='quoteitem',
        name='vat_rate',
        field=models.DecimalField(
            max_digits=5,
            decimal_places=2,
            default=Decimal('19.00'),
            help_text='MwSt.-Satz in Prozent'
        ),
    ),
]
```

**Zweck:** Individuelle MwSt.-Sätze pro Position (19%, 7%, 0%, etc.)

**Use Cases:**
- Standardsatz: 19% (Elektroinstallation)
- Ermäßigter Satz: 7% (Lieferung von Büchern)
- Befreit: 0% (Photovoltaikanlagen unter bestimmten Bedingungen)

---

## 🎨 Frontend-Features

### 1. Kompaktes Layout

**Spaltenaufteilung:**
- Linke Spalte (75%): Angebotspositionen-Tabelle
- Rechte Spalte (25%): Einstellungen, Aktionen, Metadaten

**Code:** `templates/dashboard/quote_edit.html:26-28`
```html
<div class="row g-4">
    <div class="col-lg-9">  <!-- Positionen -->
    <div class="col-lg-3">  <!-- Sidebar -->
```

### 2. Positionsnummern

Jede Position erhält automatisch eine fortlaufende Nummer (Pos. 1, Pos. 2, etc.).

**Code:** `templates/dashboard/quote_edit.html:61-62`
```html
<span class="position-number badge bg-secondary">{{ forloop.counter }}</span>
```

**JavaScript Auto-Update:** `templates/dashboard/quote_edit.html:506-514`
```javascript
function updatePositionNumbers() {
    const rows = itemsTableBody.querySelectorAll('tr.item-row');
    rows.forEach((row, index) => {
        const posNumber = row.querySelector('.position-number');
        if (posNumber) {
            posNumber.textContent = index + 1;
        }
    });
}
```

### 3. Dynamische Position hinzufügen

**Button:** "+ Position hinzufügen"

**Funktionsweise:**
1. Template `#newRowTemplate` wird geklont
2. Formset-Namen werden mit aktuellem Index generiert
3. Standard-MwSt. wird übernommen
4. TOTAL_FORMS Counter wird erhöht
5. Autocomplete wird initialisiert
6. Positionsnummern werden aktualisiert

**Code:** `templates/dashboard/quote_edit.html:458-493`
```javascript
addItemBtn.addEventListener('click', function() {
    const template = document.getElementById('newRowTemplate');
    const newRow = template.content.cloneNode(true).querySelector('tr');

    // Formset-Namen zuweisen
    textInput.name = `items-${formIndex}-text`;
    quantityInput.name = `items-${formIndex}-quantity`;
    priceInput.name = `items-${formIndex}-unit_price`;
    vatInput.name = `items-${formIndex}-vat_rate`;

    // Standard-MwSt übernehmen
    const defaultVat = parseFloat(vatRateInput.value) || 19;
    vatInput.value = defaultVat.toFixed(2);

    itemsTableBody.appendChild(newRow);
    formIndex++;
    totalFormsInput.value = formIndex;

    updatePositionNumbers();
    recalculateAll();
    initializeAutocomplete(textInput);
    textInput.focus();
});
```

### 4. Produktkatalog-Autocomplete

**Features:**
- Suche ab 2 Zeichen
- Debouncing (300ms Verzögerung)
- Tastatursteuerung (↑↓ Enter Escape)
- Auto-Population von Preis und MwSt.

**API-Endpoint:** `apps/core/dashboard_views.py:1434-1462`
```python
class ProductAutocompleteView(LoginRequiredMixin, View):
    """JSON API für Produkt-Autocomplete"""

    def get(self, request):
        query = request.GET.get('q', '').strip()

        if len(query) < 2:
            return JsonResponse({'results': []})

        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query),
            is_active=True
        ).select_related('category')[:10]

        results = [{
            'id': product.id,
            'text': product.name,
            'sku': product.sku,
            'price': float(product.sales_price_net),
            'vat_rate': float(product.vat_rate),
            'unit': product.unit,
            'category': product.category.name if product.category else '',
        } for product in products]

        return JsonResponse({'results': results})
```

**Frontend-Implementierung:** `templates/dashboard/quote_edit.html:605-702`

**Tastatursteuerung:**
- **↓ (ArrowDown):** Nächstes Ergebnis
- **↑ (ArrowUp):** Vorheriges Ergebnis
- **Enter:** Aktuelles Ergebnis auswählen
- **Escape:** Dropdown schließen

**Auto-Befüllung:**
```javascript
function selectItem(item) {
    const row = inputElement.closest('tr');
    inputElement.value = item.text;
    row.querySelector('input[name*="unit_price"]').value = item.price.toFixed(2);
    row.querySelector('input[name*="vat_rate"]').value = item.vat_rate.toFixed(2);
    dropdown.style.display = 'none';
    recalculateAll();
}
```

### 5. MwSt.-Satz pro Position

Jede Position hat ein eigenes MwSt.-Feld mit Input-Group-Styling.

**Code:** `templates/dashboard/quote_edit.html:81-87`
```html
<td>
    <div class="input-group input-group-sm">
        {{ form.vat_rate }}
        <span class="input-group-text">%</span>
    </div>
</td>
```

### 6. Split-MwSt.-Anzeige

Bei unterschiedlichen MwSt.-Sätzen wird jeder Satz einzeln ausgewiesen.

**Beispiel:**
```
Zwischensumme (netto): 5.000,00 €
MwSt. 7,00% von 1.000,00 €: 70,00 €
MwSt. 19,00% von 4.000,00 €: 760,00 €
Gesamtsumme (brutto): 5.830,00 €
```

**Code:** `templates/dashboard/quote_edit.html:584-597`
```javascript
// MwSt-Aufschlüsselung anzeigen
const vatBreakdownBody = document.getElementById('vatBreakdownBody');
vatBreakdownBody.innerHTML = '';

const sortedVatRates = Object.keys(vatBreakdown).sort((a, b) => parseFloat(a) - parseFloat(b));
sortedVatRates.forEach(key => {
    const vat = vatBreakdown[key];
    const row = document.createElement('tr');
    row.innerHTML = `
        <td colspan="5" class="text-end">MwSt. ${vat.rate.toLocaleString('de-DE', {minimumFractionDigits: 2})}% von ${vat.net.toLocaleString('de-DE', {minimumFractionDigits: 2})} €:</td>
        <td colspan="2">${vat.vat.toLocaleString('de-DE', {minimumFractionDigits: 2})} €</td>
    `;
    vatBreakdownBody.appendChild(row);
});
```

### 7. Echtzeit-Berechnung

Alle Summen werden bei jeder Änderung automatisch neu berechnet.

**Trigger:**
- Input in Menge, Einzelpreis, MwSt.-Satz
- Position hinzufügen/löschen
- DELETE-Checkbox ändern

**Code:** `templates/dashboard/quote_edit.html:539-603`
```javascript
function recalculateAll() {
    let subtotal = 0;
    const vatBreakdown = {}; // {vatRate: {rate, net, vat}}

    // Alle Zeilen durchlaufen
    const rows = itemsTableBody.querySelectorAll('tr.item-row');
    rows.forEach(row => {
        // Gelöschte Zeilen überspringen
        const deleteCheckbox = row.querySelector('input[type="checkbox"][name*="DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) {
            row.style.opacity = '0.5';
            row.style.textDecoration = 'line-through';
            return;
        }

        const lineData = calculateLineTotal(row);
        subtotal += lineData.total;

        // Nach MwSt-Satz gruppieren
        const vatKey = lineData.vatRate.toFixed(2);
        if (!vatBreakdown[vatKey]) {
            vatBreakdown[vatKey] = {rate: lineData.vatRate, net: 0, vat: 0};
        }
        vatBreakdown[vatKey].net += lineData.total;
    });

    // MwSt berechnen
    let totalVat = 0;
    for (let key in vatBreakdown) {
        vatBreakdown[key].vat = vatBreakdown[key].net * (vatBreakdown[key].rate / 100);
        totalVat += vatBreakdown[key].vat;
    }

    const total = subtotal + totalVat;

    // Display aktualisieren
    // ...
}
```

### 8. Gelöschte Positionen visualisieren

**Verhalten:**
- Bestehende Positionen: DELETE-Checkbox (Django Formset Standard)
- Neue Positionen: X-Button (entfernt sofort aus DOM)

**Visuelle Kennzeichnung gelöschter Zeilen:**
```javascript
if (deleteCheckbox && deleteCheckbox.checked) {
    row.style.opacity = '0.5';
    row.style.textDecoration = 'line-through';
}
```

---

## 🔧 Backend-Logik

### QuoteEditView

**Datei:** `apps/core/dashboard_views.py:1383-1431`

**GET-Methode:**
```python
def get(self, request, pk):
    quote = get_object_or_404(Quote.objects.select_related('precheck__site__customer'), pk=pk)
    quote_form = QuoteEditForm(instance=quote)
    items_formset = QuoteItemFormSet(instance=quote)

    context = {
        'quote': quote,
        'quote_form': quote_form,
        'items_formset': items_formset,
    }
    return render(request, self.template_name, context)
```

**POST-Methode:**
```python
def post(self, request, pk):
    quote = get_object_or_404(Quote.objects.select_related('precheck__site__customer'), pk=pk)
    quote_form = QuoteEditForm(request.POST, instance=quote)
    items_formset = QuoteItemFormSet(request.POST, instance=quote)

    if quote_form.is_valid() and items_formset.is_valid():
        quote_form.save(commit=False)
        items_formset.save()

        # Neuberechnung der Summen
        quote.subtotal = sum(item.line_total for item in quote.items.all())
        quote.save()  # Triggert automatisch vat_amount und total Berechnung

        messages.success(request, f'Angebot {quote.quote_number} wurde erfolgreich aktualisiert.')
        return redirect('dashboard:quote_detail', pk=quote.pk)

    else:
        messages.error(request, 'Fehler beim Speichern. Bitte überprüfen Sie Ihre Eingaben.')
        context = {
            'quote': quote,
            'quote_form': quote_form,
            'items_formset': items_formset,
        }
        return render(request, self.template_name, context)
```

**Wichtig:** Die Neuberechnung erfolgt in zwei Schritten:
1. `quote.subtotal` wird manuell gesetzt (Summe aller QuoteItems)
2. `quote.save()` triggert automatische Berechnung von `vat_amount` und `total` (siehe Quote Model)

### QuoteItemFormSet

**Datei:** `apps/core/forms.py:471-481`

```python
QuoteItemFormSet = forms.inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    extra=0,  # Keine automatischen leeren Zeilen
    can_delete=True,  # DELETE-Checkbox für bestehende Items
    min_num=0,
    validate_min=False,
)
```

**Wichtige Parameter:**
- `extra=0`: Keine automatisch generierten leeren Zeilen (werden via JavaScript hinzugefügt)
- `can_delete=True`: Ermöglicht Löschen von bestehenden Positionen via Checkbox
- `min_num=0`: Erlaubt Angebote ohne Positionen (theoretisch)

---

## 🎯 Use Cases

### Use Case 1: Kunde liefert eigenes Material

**Szenario:**
- Kunde hat bereits einen BYD 19kW Speicher gekauft
- Speicher soll nicht berechnet werden
- Nur Installation wird berechnet

**Lösung:**
1. Angebot öffnen und bearbeiten
2. Speicher-Position löschen (DELETE-Checkbox)
3. Neue Position hinzufügen: "Installation BYD 19kW (Kundenmaterial)"
4. Preis anpassen: Nur Arbeitskosten ohne Material
5. Notiz hinzufügen: "Speicher wird vom Kunden gestellt"
6. Speichern

### Use Case 2: Zusatzwunsch aus Freitextfeld

**Szenario:**
- Kunde hat im Precheck-Notizfeld geschrieben: "Zusätzlich Überspannungsschutz Typ 1+2"
- Muss manuell zum Angebot hinzugefügt werden

**Lösung:**
1. Angebot öffnen und bearbeiten
2. "+ Position hinzufügen" klicken
3. "Über" eintippen → Autocomplete zeigt "Überspannungsschutz Typ 1+2"
4. Mit Enter auswählen → Preis wird automatisch befüllt
5. Menge anpassen falls nötig
6. Speichern

### Use Case 3: Unterschiedliche MwSt.-Sätze

**Szenario:**
- PV-Anlage: 0% MwSt. (Nullsteuersatz seit 2023 für bestimmte Fälle)
- Installation: 19% MwSt.
- Zusatzleistung (Beratung): 19% MwSt.

**Lösung:**
1. Angebot öffnen und bearbeiten
2. PV-Material-Positionen: MwSt. auf 0% setzen
3. Installations-Positionen: MwSt. auf 19% belassen
4. Speichern
5. Angebot zeigt Split-MwSt.-Berechnung:
   - MwSt. 0,00% von 8.000,00 €: 0,00 €
   - MwSt. 19,00% von 2.000,00 €: 380,00 €
   - Gesamt: 10.380,00 €

---

## 📝 Formulare

### QuoteEditForm

**Datei:** `apps/core/forms.py:427-469`

```python
class QuoteEditForm(forms.ModelForm):
    """Form für Bearbeitung von Angebots-Metadaten"""

    class Meta:
        model = Quote
        fields = ['status', 'vat_rate', 'valid_until', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 4,
                'placeholder': 'Interne Notizen zu Sonderwünschen oder Anpassungen...',
            }),
        }
        labels = {
            'status': 'Status',
            'vat_rate': 'Standard-MwSt.',
            'valid_until': 'Gültig bis',
            'notes': 'Interne Notizen',
        }
        help_texts = {
            'status': 'Aktueller Bearbeitungsstand des Angebots',
            'valid_until': 'Datum bis zu dem das Angebot gültig ist',
            'notes': 'Wird nur intern angezeigt, nicht im Kunden-PDF',
        }
```

### QuoteItemForm

**Datei:** `apps/core/forms.py:367-424`

```python
class QuoteItemForm(forms.ModelForm):
    """Form für Bearbeitung einzelner Angebotspositionen"""

    class Meta:
        model = QuoteItem
        fields = ['text', 'quantity', 'unit_price', 'vat_rate']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control form-control-sm autocomplete-product',
                'placeholder': 'Bezeichnung eingeben oder aus Katalog wählen...',
                'autocomplete': 'off',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '1.00',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '19',
            }),
        }
        labels = {
            'text': 'Bezeichnung',
            'quantity': 'Menge',
            'unit_price': 'Einzelpreis',
            'vat_rate': 'MwSt. %',
        }
```

---

## 🔗 URL-Routing

**Datei:** `apps/core/dashboard_urls.py`

### Quote Edit
```python
path('quotes/<int:pk>/edit/',
     dashboard_views.QuoteEditView.as_view(),
     name='quote_edit'),
```

**Beispiel:** `/dashboard/quotes/42/edit/`

### Product Autocomplete API
```python
path('api/products/autocomplete/',
     dashboard_views.ProductAutocompleteView.as_view(),
     name='product_autocomplete'),
```

**Beispiel:** `/dashboard/api/products/autocomplete/?q=Wall`

---

## 🎨 Styling

### Kompakte Rechte Spalte

**CSS:** `templates/dashboard/quote_edit.html:444-457`

```css
.compact-form .form-select,
.compact-form .form-control,
.compact-form textarea {
    font-size: 12px;
    padding: 0.375rem 0.5rem;
}

.compact-form textarea {
    font-size: 11px;
}

.compact-form .input-group-sm .form-control {
    font-size: 11px;
}
```

**Labels & Hilfetext:**
```html
<label class="form-label" style="font-size: 12px; margin-bottom: 4px;">
<div class="form-text" style="font-size: 10px;">
```

### Autocomplete Dropdown

```css
.autocomplete-dropdown {
    position: absolute;
    z-index: 1000;
    background: white;
    border: 1px solid var(--neutral-300);
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    max-height: 300px;
    overflow-y: auto;
    width: calc(100% - 30px);
    margin-top: 2px;
}

.autocomplete-item {
    padding: 10px 12px;
    cursor: pointer;
    transition: background-color 0.15s;
}

.autocomplete-item.selected {
    background-color: var(--primary-blue);
    color: white;
}
```

---

## 🧪 Testing

### Manueller Test-Flow

1. **Angebot erstellen:**
   ```bash
   # Precheck durchführen
   http://192.168.178.30:8025/precheck/
   ```

2. **Angebot öffnen:**
   ```
   http://192.168.178.30:8025/dashboard/quotes/
   → Angebot auswählen → "Bearbeiten" klicken
   ```

3. **Features testen:**
   - [ ] Position hinzufügen mit + Button
   - [ ] Autocomplete: "Wall" eintippen
   - [ ] Tastatursteuerung: ↓ ↑ Enter
   - [ ] MwSt.-Satz ändern (7%, 19%)
   - [ ] Position löschen (DELETE checkbox)
   - [ ] Echtzeit-Berechnung prüfen
   - [ ] Split-MwSt.-Anzeige bei unterschiedlichen Sätzen
   - [ ] Speichern und Summen-Neuberechnung prüfen

### API-Test (Autocomplete)

```bash
# Produkt-Suche
curl "http://192.168.178.30:8025/dashboard/api/products/autocomplete/?q=Wall"

# Erwartete Response:
{
  "results": [
    {
      "id": 15,
      "text": "Wallbox 11kW inkl. Installation",
      "sku": "WB-11KW-01",
      "price": 1290.00,
      "vat_rate": 19.00,
      "unit": "Stk",
      "category": "Wallbox"
    }
  ]
}
```

---

## 📊 Datenbankabfragen

### Alle Angebote mit Items laden

```python
from apps.quotes.models import Quote

quote = Quote.objects.select_related(
    'precheck__site__customer'
).prefetch_related('items').get(pk=42)

print(quote.quote_number)
print(quote.items.count())
```

### Items mit unterschiedlichen MwSt.-Sätzen

```python
from apps.quotes.models import QuoteItem
from django.db.models import Sum, F

# Gruppiere nach MwSt.-Satz
vat_breakdown = QuoteItem.objects.filter(quote_id=42).values('vat_rate').annotate(
    net_total=Sum(F('quantity') * F('unit_price'))
)

for entry in vat_breakdown:
    print(f"MwSt {entry['vat_rate']}%: {entry['net_total']} €")
```

---

## 🐛 Known Issues & Solutions

### Issue 1: Formset Management Form fehlt

**Symptom:** "ManagementForm data is missing"

**Lösung:**
```html
{{ items_formset.management_form }}
```

Muss im Template vorhanden sein, enthält:
- TOTAL_FORMS
- INITIAL_FORMS
- MIN_NUM_FORMS
- MAX_NUM_FORMS

### Issue 2: Neue Zeilen werden nicht gespeichert

**Ursache:** Formset-Namen falsch generiert

**Lösung:** Korrekte Namenskonvention:
```javascript
textInput.name = `items-${formIndex}-text`;  // ✅ Richtig
textInput.name = `item-${formIndex}-text`;   // ❌ Falsch
```

### Issue 3: TOTAL_FORMS nicht inkrementiert

**Symptom:** Django ignoriert neue Zeilen beim Speichern

**Lösung:**
```javascript
formIndex++;
totalFormsInput.value = formIndex;  // Wichtig!
```

### Issue 4: Autocomplete-Dropdown verschwindet hinter anderen Elementen

**Lösung:**
```css
.autocomplete-dropdown {
    z-index: 1000;  /* Muss höher sein als Tabellen-z-index */
}
```

---

## 🚀 Zukünftige Erweiterungen

### Geplante Features

1. **Inline-Bearbeitung in Tabelle**
   - Doppelklick auf Zelle → Edit-Modus
   - Enter speichert, Escape bricht ab

2. **Positionskopie**
   - Button "Duplizieren" für schnelles Hinzufügen ähnlicher Positionen

3. **Preishistorie**
   - Tracking aller Änderungen an Positionen
   - Audit-Log für Compliance

4. **Bulk-Import**
   - CSV-Upload für große Positionslisten
   - Excel-Template-Download

5. **Positionen-Vorlagen**
   - Häufig verwendete Positionskombinationen speichern
   - "Standard-Installationspaket" mit einem Klick hinzufügen

6. **Rabatte pro Position**
   - Prozentuale oder absolute Rabatte
   - Rabatt-Grund-Feld

---

## 📚 Weiterführende Dokumentation

- **[CLAUDE_DATABASE.md](CLAUDE_DATABASE.md)** - Quote & QuoteItem Models
- **[CLAUDE_ADMIN.md](CLAUDE_ADMIN.md)** - Dashboard-System
- **[CLAUDE_PRODUKTKATALOG.md](CLAUDE_PRODUKTKATALOG.md)** - Product & ProductCategory Models
- **[CLAUDE_API.md](CLAUDE_API.md)** - API-Endpoints

---

**Letzte Aktualisierung:** 2025-01-16
**Version:** 1.3.0
