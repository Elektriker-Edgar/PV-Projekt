"""
Django Forms für EDGARD PV-Service Dashboard

Forms für das Admin-Dashboard mit Validierung und Custom Widgets
"""
from django import forms
from decimal import Decimal, InvalidOperation
from apps.quotes.models import PriceConfig, ProductCategory, Product
from apps.customers.models import Customer


class PriceConfigForm(forms.ModelForm):
    """
    Form für Bearbeitung von Preiskonfigurationen

    Features:
    - Validierung für value (muss positiv sein, außer bei Rabatten)
    - Custom Widgets mit Bootstrap-Klassen
    - Help-Text für bessere UX
    - Read-only price_type Feld
    """

    class Meta:
        model = PriceConfig
        fields = ['price_type', 'value', 'is_percentage', 'description']
        widgets = {
            'price_type': forms.Select(attrs={
                'class': 'form-control',
                'disabled': 'disabled',  # Typ kann nicht geändert werden
            }),
            'value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'z.B. 150.00',
            }),
            'is_percentage': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optionale Beschreibung',
            }),
        }
        labels = {
            'price_type': 'Preistyp',
            'value': 'Wert',
            'is_percentage': 'Prozentangabe',
            'description': 'Beschreibung',
        }
        help_texts = {
            'price_type': 'Der Typ kann nicht geändert werden.',
            'value': 'Betrag in Euro oder Prozent (abhängig von "Prozentangabe")',
            'is_percentage': 'Aktivieren, wenn der Wert ein Prozentsatz ist (z.B. für Rabatte)',
            'description': 'Zusätzliche Informationen (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # price_type ist read-only, aber wir müssen es für die Validierung behalten
        # Daher disabled im Widget, aber im clean-Prozess wiederherstellen
        if self.instance and self.instance.pk:
            self.fields['price_type'].disabled = True

        # Custom Labels basierend auf Typ
        if self.instance and self.instance.pk:
            display_name = self.instance.get_price_type_display()
            self.fields['price_type'].label = f'Preistyp: {display_name}'

            # Dynamischer Platzhalter basierend auf is_percentage
            if self.instance.is_percentage:
                self.fields['value'].widget.attrs['placeholder'] = 'z.B. 10.00 (für 10%)'
                self.fields['value'].widget.attrs['step'] = '0.01'
            else:
                self.fields['value'].widget.attrs['placeholder'] = 'z.B. 150.00 (in Euro)'
                self.fields['value'].widget.attrs['step'] = '0.01'

    def clean_value(self):
        """
        Validierung für value-Feld

        - Muss eine gültige Decimal-Zahl sein
        - Bei Rabatten (discount_*) kann negativ sein
        - Sonst muss >= 0 sein
        - Maximal 2 Nachkommastellen
        """
        value = self.cleaned_data.get('value')

        if value is None:
            raise forms.ValidationError('Bitte geben Sie einen Wert ein.')

        # Konvertierung zu Decimal
        try:
            value = Decimal(str(value))
        except (ValueError, InvalidOperation):
            raise forms.ValidationError('Bitte geben Sie eine gültige Zahl ein.')

        # Prüfe auf zu viele Nachkommastellen
        # Decimal hat ein tuple als 'as_tuple().digits'
        decimal_places = abs(value.as_tuple().exponent)
        if decimal_places > 2:
            raise forms.ValidationError('Maximal 2 Nachkommastellen erlaubt.')

        # Rabatte dürfen negativ sein, andere Werte nicht
        price_type = self.cleaned_data.get('price_type') or (
            self.instance.price_type if self.instance else None
        )

        if price_type and not price_type.startswith('discount_'):
            if value < 0:
                raise forms.ValidationError('Der Wert muss positiv sein (außer bei Rabatten).')

        # Prozentangaben validieren
        is_percentage = self.cleaned_data.get('is_percentage') or (
            self.instance.is_percentage if self.instance else False
        )

        if is_percentage:
            if value < 0 or value > 100:
                raise forms.ValidationError('Prozentangaben müssen zwischen 0 und 100 liegen.')

        return value

    def clean_description(self):
        """
        Validierung für description-Feld

        - Maximale Länge 200 Zeichen
        - Trimmen von Whitespace
        """
        description = self.cleaned_data.get('description', '').strip()

        if len(description) > 200:
            raise forms.ValidationError('Die Beschreibung darf maximal 200 Zeichen lang sein.')

        return description

    def clean(self):
        """
        Form-weite Validierung

        Stelle sicher, dass price_type bei Update nicht geändert wird
        """
        cleaned_data = super().clean()

        # Bei Update: price_type wiederherstellen (falls disabled-Field nicht mitgeschickt wird)
        if self.instance and self.instance.pk:
            cleaned_data['price_type'] = self.instance.price_type

        # Logische Validierung: is_percentage und value
        is_percentage = cleaned_data.get('is_percentage')
        value = cleaned_data.get('value')

        if is_percentage and value is not None:
            if value > 100:
                self.add_error('value', 'Prozentangaben können nicht größer als 100% sein.')

        return cleaned_data

    def save(self, commit=True):
        """
        Speichern mit zusätzlicher Logik

        - Stelle sicher, dass price_type nicht überschrieben wird
        """
        instance = super().save(commit=False)

        # Bei Update: price_type darf nicht geändert werden
        if self.instance.pk:
            instance.price_type = self.instance.price_type

        if commit:
            instance.save()

        return instance


class PriceConfigBulkUpdateForm(forms.Form):
    """
    Form für Bulk-Update mehrerer Preiskonfigurationen

    Optional: Kann für zukünftige Features verwendet werden
    z.B. "Alle Preise um X% erhöhen"
    """

    percentage_change = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=True,
        label='Prozentuale Änderung',
        help_text='Positive Zahl = Erhöhung, Negative Zahl = Reduzierung (z.B. 5.00 für +5%, -10.00 für -10%)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'z.B. 5.00',
        })
    )

    price_types = forms.MultipleChoiceField(
        choices=PriceConfig.PRICE_TYPES,
        required=True,
        label='Betroffene Preistypen',
        help_text='Wählen Sie die Preistypen aus, die geändert werden sollen',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        })
    )

    def clean_percentage_change(self):
        """
        Validierung für percentage_change

        - Muss zwischen -100 und +1000 liegen (sinnvolle Grenzen)
        """
        percentage = self.cleaned_data.get('percentage_change')

        if percentage is None:
            raise forms.ValidationError('Bitte geben Sie eine prozentuale Änderung ein.')

        if percentage < -100:
            raise forms.ValidationError('Reduzierung darf nicht größer als -100% sein.')

        if percentage > 1000:
            raise forms.ValidationError('Erhöhung darf nicht größer als 1000% sein.')

        if percentage == 0:
            raise forms.ValidationError('Die Änderung muss ungleich 0 sein.')

        return percentage

    def apply_changes(self):
        """
        Wendet die Änderungen auf die ausgewählten PriceConfigs an

        Returns:
            int: Anzahl der aktualisierten Datensätze
        """
        percentage = self.cleaned_data.get('percentage_change')
        price_types = self.cleaned_data.get('price_types')

        if not percentage or not price_types:
            return 0

        # Berechne Multiplikator
        multiplier = Decimal('1') + (percentage / Decimal('100'))

        # Aktualisiere alle ausgewählten PriceConfigs
        updated_count = 0
        for price_type in price_types:
            try:
                config = PriceConfig.objects.get(price_type=price_type)

                # Nur nicht-prozentuale Werte ändern (Euro-Beträge)
                if not config.is_percentage:
                    old_value = config.value
                    new_value = (old_value * multiplier).quantize(Decimal('0.01'))
                    config.value = new_value
                    config.save()
                    updated_count += 1
            except PriceConfig.DoesNotExist:
                continue

        return updated_count


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
