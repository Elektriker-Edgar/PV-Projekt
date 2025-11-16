"""
Django Forms für EDGARD PV-Service Dashboard

Forms für das Admin-Dashboard mit Validierung und Custom Widgets
"""
from django import forms
from decimal import Decimal, InvalidOperation
from apps.quotes.models import ProductCategory, Product, Quote, QuoteItem
from apps.customers.models import Customer


class CustomerSearchForm(forms.Form):
    """
    Such-Formular für Kunden

    Optional: Kann für erweiterte Suchfunktionen verwendet werden
    """

    search_query = forms.CharField(
        max_length=200,
        required=False,
        label='Suche',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name, E-Mail, Telefon...',
        })
    )

    customer_type = forms.ChoiceField(
        choices=[('', 'Alle Typen')] + list(Customer.CUSTOMER_TYPES),
        required=False,
        label='Kundentyp',
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    def clean_search_query(self):
        """
        Trimme Suchbegriff
        """
        return self.cleaned_data.get('search_query', '').strip()


class ProductCategoryForm(forms.ModelForm):
    """
    Form für Bearbeitung von Produktkategorien

    Features:
    - Validierung für eindeutige Namen
    - Custom Widgets mit Bootstrap-Klassen
    - Sort-Order Validierung
    """

    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Installationsmaterial',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Beschreibung der Kategorie (optional)',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'z.B. 10',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'name': 'Kategoriename',
            'description': 'Beschreibung',
            'sort_order': 'Sortierreihenfolge',
            'is_active': 'Aktiv',
        }
        help_texts = {
            'name': 'Eindeutiger Name der Kategorie',
            'description': 'Zusätzliche Informationen (optional)',
            'sort_order': 'Niedrigere Werte werden zuerst angezeigt',
            'is_active': 'Inaktive Kategorien werden ausgeblendet',
        }

    def clean_name(self):
        """
        Validierung für name-Feld

        - Muss eindeutig sein (außer bei Update desselben Objekts)
        - Darf nicht leer sein
        - Maximale Länge 200 Zeichen
        """
        name = self.cleaned_data.get('name', '').strip()

        if not name:
            raise forms.ValidationError('Kategoriename darf nicht leer sein.')

        # Prüfe auf Duplikate (außer bei Update desselben Objekts)
        queryset = ProductCategory.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(f'Eine Kategorie mit dem Namen "{name}" existiert bereits.')

        if len(name) > 200:
            raise forms.ValidationError('Der Name darf maximal 200 Zeichen lang sein.')

        return name

    def clean_sort_order(self):
        """
        Validierung für sort_order

        - Muss >= 0 sein
        """
        sort_order = self.cleaned_data.get('sort_order')

        if sort_order is None:
            return 0

        if sort_order < 0:
            raise forms.ValidationError('Die Sortierreihenfolge muss >= 0 sein.')

        return sort_order


class ProductForm(forms.ModelForm):
    """
    Form für Bearbeitung von Produkten

    Features:
    - Validierung für eindeutige SKU
    - Preisvalidierung (Verkaufspreis >= Einkaufspreis)
    - Automatische Berechnung von Margen
    - Custom Widgets mit Bootstrap-Klassen
    """

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'sku', 'description', 'unit',
            'purchase_price_net', 'sales_price_net', 'vat_rate',
            'stock_quantity', 'min_stock_level',
            'manufacturer', 'supplier', 'notes',
            'is_active', 'is_featured'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. AC-Kabel 5x10mm²',
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. AC-CABLE-5X10',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Produktbeschreibung (optional)',
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select',
            }),
            'purchase_price_net': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'sales_price_net': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'vat_rate': forms.Select(attrs={
                'class': 'form-select',
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0',
            }),
            'min_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0',
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Fronius',
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Elektro-Großhandel',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Interne Notizen (optional)',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'category': 'Kategorie',
            'name': 'Bezeichnung',
            'sku': 'Artikelnummer',
            'description': 'Beschreibung',
            'unit': 'Einheit',
            'purchase_price_net': 'Einkaufspreis (netto)',
            'sales_price_net': 'Verkaufspreis (netto)',
            'vat_rate': 'MwSt.-Satz',
            'stock_quantity': 'Lagerbestand',
            'min_stock_level': 'Mindestbestand',
            'manufacturer': 'Hersteller',
            'supplier': 'Lieferant',
            'notes': 'Notizen',
            'is_active': 'Aktiv',
            'is_featured': 'Hervorgehoben',
        }
        help_texts = {
            'sku': 'Eindeutige Artikelnummer (z.B. AC-CABLE-5X10)',
            'unit': 'Verkaufseinheit (Stück, Meter, etc.)',
            'purchase_price_net': 'Netto-Einkaufspreis in Euro',
            'sales_price_net': 'Netto-Verkaufspreis in Euro',
            'vat_rate': 'Mehrwertsteuersatz',
            'stock_quantity': 'Aktueller Lagerbestand (optional)',
            'min_stock_level': 'Mindestbestand für Warnungen (optional)',
            'is_active': 'Inaktive Produkte werden ausgeblendet',
            'is_featured': 'Hervorgehobene Produkte für schnellen Zugriff',
        }

    def clean_sku(self):
        """
        Validierung für SKU (Artikelnummer)

        - Muss eindeutig sein (außer bei Update desselben Objekts)
        - Darf nicht leer sein
        - Maximale Länge 100 Zeichen
        - Nur alphanumerische Zeichen + Bindestrich/Unterstrich
        """
        sku = self.cleaned_data.get('sku', '').strip().upper()

        if not sku:
            raise forms.ValidationError('Artikelnummer darf nicht leer sein.')

        # Prüfe auf Duplikate (außer bei Update desselben Objekts)
        queryset = Product.objects.filter(sku=sku)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(f'Ein Produkt mit der Artikelnummer "{sku}" existiert bereits.')

        if len(sku) > 100:
            raise forms.ValidationError('Die Artikelnummer darf maximal 100 Zeichen lang sein.')

        # Erlaube nur alphanumerische Zeichen + Bindestrich/Unterstrich
        import re
        if not re.match(r'^[A-Z0-9_-]+$', sku):
            raise forms.ValidationError(
                'Die Artikelnummer darf nur Buchstaben, Zahlen, Bindestriche und Unterstriche enthalten.'
            )

        return sku

    def clean_name(self):
        """
        Validierung für name

        - Darf nicht leer sein
        - Maximale Länge 200 Zeichen
        """
        name = self.cleaned_data.get('name', '').strip()

        if not name:
            raise forms.ValidationError('Produktname darf nicht leer sein.')

        if len(name) > 200:
            raise forms.ValidationError('Der Produktname darf maximal 200 Zeichen lang sein.')

        return name

    def clean_purchase_price_net(self):
        """
        Validierung für Einkaufspreis

        - Muss >= 0 sein
        - Maximal 2 Nachkommastellen
        """
        price = self.cleaned_data.get('purchase_price_net')

        if price is None:
            return Decimal('0.00')

        if price < 0:
            raise forms.ValidationError('Der Einkaufspreis muss >= 0 sein.')

        # Prüfe auf zu viele Nachkommastellen
        decimal_places = abs(price.as_tuple().exponent)
        if decimal_places > 2:
            raise forms.ValidationError('Maximal 2 Nachkommastellen erlaubt.')

        return price

    def clean_sales_price_net(self):
        """
        Validierung für Verkaufspreis

        - Muss >= 0 sein
        - Maximal 2 Nachkommastellen
        """
        price = self.cleaned_data.get('sales_price_net')

        if price is None:
            raise forms.ValidationError('Bitte geben Sie einen Verkaufspreis ein.')

        if price < 0:
            raise forms.ValidationError('Der Verkaufspreis muss >= 0 sein.')

        # Prüfe auf zu viele Nachkommastellen
        decimal_places = abs(price.as_tuple().exponent)
        if decimal_places > 2:
            raise forms.ValidationError('Maximal 2 Nachkommastellen erlaubt.')

        return price

    def clean(self):
        """
        Form-weite Validierung

        - Verkaufspreis sollte >= Einkaufspreis sein (Warnung)
        """
        cleaned_data = super().clean()

        purchase_price = cleaned_data.get('purchase_price_net')
        sales_price = cleaned_data.get('sales_price_net')

        if purchase_price and sales_price:
            if sales_price < purchase_price:
                self.add_error(
                    'sales_price_net',
                    forms.ValidationError(
                        'WARNUNG: Verkaufspreis ist niedriger als Einkaufspreis. '
                        'Dies führt zu einem negativen Deckungsbeitrag.',
                        code='negative_margin'
                    )
                )

        return cleaned_data


class QuoteItemForm(forms.ModelForm):
    """
    Form für Bearbeitung einzelner Angebotspositionen
    """

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
                'step': '1',
                'min': '0',
                'max': '100',
                'placeholder': '19',
            }),
        }
        labels = {
            'text': 'Bezeichnung',
            'quantity': 'Menge',
            'unit_price': 'Einzelpreis (€)',
            'vat_rate': 'MwSt. %',
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError('Die Menge muss größer als 0 sein.')
        return quantity

    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is not None and price < 0:
            raise forms.ValidationError('Der Preis darf nicht negativ sein.')
        return price


# Django Formsets für dynamisches Hinzufügen/Entfernen von QuoteItems
QuoteItemFormSet = forms.inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    extra=0,  # Keine automatisch leere Zeile - wird per JavaScript hinzugefügt
    can_delete=True,  # Positionen können gelöscht werden
    min_num=0,  # Keine Mindestanzahl (erlaubt leere Angebote während Bearbeitung)
    validate_min=False,
)


class QuoteEditForm(forms.ModelForm):
    """
    Form für Bearbeitung von Angeboten

    Ermöglicht das Anpassen von:
    - Status
    - Gültigkeitsdauer
    - MwSt-Satz
    - Notizen/Anmerkungen
    """

    notes = forms.CharField(
        required=False,
        label='Interne Notizen / Anmerkungen',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Z.B. Kundenwünsche, Sonderkonditionen, eigenes Material des Kunden...',
        }),
        help_text='Werden nicht auf dem PDF angezeigt, nur intern sichtbar'
    )

    class Meta:
        model = Quote
        fields = ['status', 'vat_rate', 'valid_until', 'notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0',
                'max': '100',
                'placeholder': '19',
            }),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }
        labels = {
            'status': 'Status',
            'vat_rate': 'MwSt.-Satz (%)',
            'valid_until': 'Gültig bis',
        }
        help_texts = {
            'status': 'Aktueller Bearbeitungsstatus des Angebots',
            'vat_rate': 'Mehrwertsteuersatz in Prozent (Standard: 19%)',
            'valid_until': 'Datum bis wann das Angebot gültig ist',
        }

    def clean_vat_rate(self):
        vat_rate = self.cleaned_data.get('vat_rate')
        if vat_rate is not None:
            if vat_rate < 0 or vat_rate > 100:
                raise forms.ValidationError('Der MwSt.-Satz muss zwischen 0% und 100% liegen.')
        return vat_rate
