"""
Django Forms für EDGARD PV-Service Dashboard

Forms für das Admin-Dashboard mit Validierung und Custom Widgets
"""
from django import forms
from decimal import Decimal, InvalidOperation
from apps.quotes.models import PriceConfig
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


# Import für CustomerSearchForm
from apps.customers.models import Customer
