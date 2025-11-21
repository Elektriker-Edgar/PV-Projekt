"""
Dashboard URL Configuration
Admin-Dashboard URLs für EDGARD PV-Service

Alle URLs sind unter /dashboard/ verfügbar
"""
from django.urls import path
from . import dashboard_views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard Home - Übersicht mit Statistiken
    path('', dashboard_views.DashboardHomeView.as_view(), name='home'),

    # Precheck Management
    path('prechecks/', dashboard_views.PrecheckListView.as_view(), name='precheck_list'),
    path('prechecks/<int:pk>/', dashboard_views.PrecheckDetailView.as_view(), name='precheck_detail'),
    path('prechecks/<int:pk>/delete/', dashboard_views.PrecheckDeleteView.as_view(), name='precheck_delete'),
    path('prechecks/<int:pk>/pdf/', dashboard_views.PrecheckPDFExportView.as_view(), name='precheck_pdf'),
    path('prechecks/export/', dashboard_views.PrecheckExportView.as_view(), name='precheck_export'),

    # Customer Management
    path('customers/', dashboard_views.CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', dashboard_views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/delete/', dashboard_views.CustomerDeleteView.as_view(), name='customer_delete'),
    path('customers/bulk-delete/', dashboard_views.CustomerBulkDeleteView.as_view(), name='customer_bulk_delete'),

    # Quote Management
    path('quotes/', dashboard_views.QuoteListView.as_view(), name='quote_list'),
    path('quotes/<int:pk>/', dashboard_views.QuoteDetailView.as_view(), name='quote_detail'),
    path('quotes/<int:pk>/edit/', dashboard_views.QuoteEditView.as_view(), name='quote_edit'),
    path('quotes/bulk-delete/', dashboard_views.QuoteBulkDeleteView.as_view(), name='quote_bulk_delete'),

    # Product Catalog - Categories
    path('catalog/categories/', dashboard_views.ProductCategoryListView.as_view(), name='category_list'),
    path('catalog/categories/create/', dashboard_views.ProductCategoryCreateView.as_view(), name='category_create'),
    path('catalog/categories/<int:pk>/edit/', dashboard_views.ProductCategoryUpdateView.as_view(), name='category_update'),
    path('catalog/categories/<int:pk>/delete/', dashboard_views.ProductCategoryDeleteView.as_view(), name='category_delete'),

    # Product Catalog - Products
    path('catalog/products/', dashboard_views.ProductListView.as_view(), name='product_list'),
    path('catalog/products/bulk-action/', dashboard_views.ProductBulkActionView.as_view(), name='product_bulk_action'),
    path('catalog/products/create/', dashboard_views.ProductCreateView.as_view(), name='product_create'),
    path('catalog/products/<int:pk>/edit/', dashboard_views.ProductUpdateView.as_view(), name='product_update'),
    path('catalog/products/<int:pk>/delete/', dashboard_views.ProductDeleteView.as_view(), name='product_delete'),
    path('api/products/autocomplete/', dashboard_views.ProductAutocompleteView.as_view(), name='product_autocomplete'),

    # Product Catalog - CSV Import/Export
    path('catalog/products/export-csv/', dashboard_views.ProductExportCSVView.as_view(), name='product_export_csv'),
    path('catalog/products/import-csv/', dashboard_views.ProductImportCSVView.as_view(), name='product_import_csv'),

    # N8n Integration - System Settings
    path('settings/n8n/', dashboard_views.N8nSettingsView.as_view(), name='n8n_settings'),
    path('settings/n8n/webhook-logs/', dashboard_views.WebhookLogListView.as_view(), name='webhook_logs'),
]
