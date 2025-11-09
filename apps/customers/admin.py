from django.contrib import admin
from .models import Customer, Site


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'customer_type', 'last_quote_number', 'created_at')
    list_filter = ('customer_type', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'consent_timestamp', 'consent_ip')
    date_hierarchy = 'created_at'


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('customer', 'building_type', 'main_fuse_ampere', 'grid_type', 'created_at')
    list_filter = ('building_type', 'grid_type', 'created_at')
    search_fields = ('customer__name', 'address')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('customer',)
    date_hierarchy = 'created_at'
