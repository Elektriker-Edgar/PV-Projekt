"""
Django Admin für N8n Integration Models
"""

from django.contrib import admin
from django.utils.html import format_html
from apps.integrations.models import WebhookLog, N8nWorkflowStatus, N8nConfiguration


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    """Admin-Interface für Webhook-Logs"""

    list_display = [
        'id',
        'event_type',
        'direction',
        'status_badge',
        'precheck_id',
        'created_at',
    ]

    list_filter = [
        'status',
        'direction',
        'event_type',
        'created_at',
    ]

    search_fields = [
        'event_type',
        'error_message',
        'precheck_id',
        'quote_id',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    def status_badge(self, obj):
        """Status als farbiges Badge"""
        colors = {
            'pending': '#f59e0b',
            'success': '#10b981',
            'failed': '#ef4444',
            'retry': '#8b5cf6',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(N8nWorkflowStatus)
class N8nWorkflowStatusAdmin(admin.ModelAdmin):
    """Admin-Interface für N8n Workflow Status"""

    list_display = [
        'id',
        'precheck',
        'status',
        'created_at',
        'last_event_at',
    ]

    list_filter = [
        'status',
        'created_at',
    ]

    readonly_fields = [
        'created_at',
        'last_event_at',
        'completed_at',
    ]


@admin.register(N8nConfiguration)
class N8nConfigurationAdmin(admin.ModelAdmin):
    """Admin-Interface für N8n Konfiguration"""

    list_display = [
        'id',
        'webhook_url',
        'is_active',
        'updated_at',
    ]

    fields = [
        'webhook_url',
        'api_key',
        'is_active',
        'created_at',
        'updated_at',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Nur ein Config-Objekt erlaubt (Singleton)"""
        return not N8nConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Config darf nicht gelöscht werden"""
        return False
