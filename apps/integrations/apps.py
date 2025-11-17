from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.integrations'
    verbose_name = 'N8n Integrationen'

    def ready(self):
        """Importiere Signals wenn App geladen wird"""
        import apps.integrations.signals  # noqa
