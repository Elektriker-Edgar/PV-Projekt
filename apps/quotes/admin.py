from django.contrib import admin
from .models import Component, Precheck, Quote, QuoteItem, PrecheckPhoto


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'vendor', 'sku', 'unit_price', 'created_at')
    list_filter = ('type', 'vendor', 'created_at')
    search_fields = ('name', 'vendor', 'sku')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('compatible_with',)


class PrecheckPhotoInline(admin.TabularInline):
    model = PrecheckPhoto
    extra = 0
    readonly_fields = ('uploaded_at',)
    fields = ('category', 'photo', 'uploaded_at')


@admin.register(Precheck)
class PrecheckAdmin(admin.ModelAdmin):
    list_display = ('site', 'desired_power_kw', 'storage_kwh', 'package_choice', 'own_components', 'created_at')
    list_filter = ('package_choice', 'own_components', 'created_at')
    search_fields = ('site__customer__name', 'site__address')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('site',)
    date_hierarchy = 'created_at'
    inlines = [PrecheckPhotoInline]


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1
    readonly_fields = ('line_total',)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('quote_number', 'precheck', 'status', 'total', 'created_by', 'created_at')
    list_filter = ('status', 'created_at', 'approved_at')
    search_fields = ('quote_number', 'precheck__site__customer__name')
    readonly_fields = ('quote_number', 'vat_amount', 'total', 'created_at', 'updated_at')
    raw_id_fields = ('precheck', 'created_by', 'approved_by')
    date_hierarchy = 'created_at'
    inlines = [QuoteItemInline]
    
    actions = ['approve_quotes']
    
    def approve_quotes(self, request, queryset):
        for quote in queryset.filter(status='review'):
            quote.status = 'approved'
            quote.approved_by = request.user
            quote.save()
        self.message_user(request, f"{queryset.count()} Angebote wurden freigegeben.")
    approve_quotes.short_description = "Ausgewählte Angebote freigeben"


@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ('quote', 'text', 'quantity', 'unit_price', 'line_total')
    search_fields = ('quote__quote_number', 'text')
    readonly_fields = ('line_total',)
    raw_id_fields = ('quote', 'component')


@admin.register(PrecheckPhoto)
class PrecheckPhotoAdmin(admin.ModelAdmin):
    list_display = ('precheck', 'category', 'photo', 'uploaded_at')
    list_filter = ('category', 'uploaded_at')
    search_fields = ('precheck__site__customer__name',)
    readonly_fields = ('uploaded_at',)
    raw_id_fields = ('precheck',)
    date_hierarchy = 'uploaded_at'
