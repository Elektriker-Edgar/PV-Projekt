from django.db import models
from django.utils import timezone


class WebhookLog(models.Model):
    """
    Tracking aller Webhook-Calls zwischen Django und N8n.
    Ermöglicht Debugging und Audit-Trail für alle Integrationen.
    """

    DIRECTION_CHOICES = [
        ('outgoing', 'Django → N8n'),
        ('incoming', 'N8n → Django'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('success', 'Erfolgreich'),
        ('failed', 'Fehlgeschlagen'),
        ('retry', 'Wird wiederholt'),
    ]

    # Identifikation
    event_type = models.CharField(
        max_length=50,
        help_text='Art des Events (z.B. precheck_submitted, quote_approved)',
        db_index=True,
    )

    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        default='outgoing',
        help_text='Richtung des Webhook-Calls',
    )

    # Daten
    payload = models.JSONField(
        help_text='Gesendete/Empfangene Daten als JSON',
    )

    response = models.JSONField(
        null=True,
        blank=True,
        help_text='Antwort vom Empfänger',
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )

    error_message = models.TextField(
        blank=True,
        help_text='Fehlermeldung falls status=failed',
    )

    # Retry-Logik
    retry_count = models.IntegerField(
        default=0,
        help_text='Anzahl der Wiederholungsversuche',
    )

    # Referenzen (optional, für schnellere Suche)
    precheck_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Zugehöriger Precheck (falls relevant)',
    )

    quote_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Zugehöriges Quote (falls relevant)',
    )

    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Webhook Log'
        verbose_name_plural = 'Webhook Logs'
        indexes = [
            models.Index(fields=['-created_at', 'status']),
            models.Index(fields=['event_type', 'status']),
        ]

    def __str__(self):
        return f"{self.get_direction_display()} - {self.event_type} ({self.get_status_display()})"

    def mark_success(self, response_data=None):
        """Markiert Webhook als erfolgreich"""
        self.status = 'success'
        if response_data:
            self.response = response_data
        self.save()

    def mark_failed(self, error_message):
        """Markiert Webhook als fehlgeschlagen"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()

    def increment_retry(self):
        """Erhöht Retry-Counter"""
        self.retry_count += 1
        self.status = 'retry'
        self.save()


class N8nWorkflowStatus(models.Model):
    """
    Status-Tracking für N8n-Workflows pro Precheck/Quote.
    Ermöglicht Übersicht über den aktuellen Verarbeitungsstand.
    """

    STATUS_CHOICES = [
        ('initiated', 'Workflow gestartet'),
        ('data_validation', 'Daten werden validiert'),
        ('incomplete', 'Daten unvollständig'),
        ('waiting_customer', 'Wartet auf Kundenantwort'),
        ('generating_quote', 'Angebot wird erstellt'),
        ('quote_ready', 'Angebot fertig'),
        ('sent_to_customer', 'An Kunde versendet'),
        ('failed', 'Fehler aufgetreten'),
    ]

    # Referenzen
    precheck = models.ForeignKey(
        'quotes.Precheck',
        on_delete=models.CASCADE,
        related_name='workflow_statuses',
        null=True,
        blank=True,
    )

    quote = models.ForeignKey(
        'quotes.Quote',
        on_delete=models.CASCADE,
        related_name='workflow_statuses',
        null=True,
        blank=True,
    )

    # Workflow-Daten
    workflow_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='N8n Workflow Execution ID',
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='initiated',
        db_index=True,
    )

    # KI-Validierung (optional)
    ai_validation_result = models.JSONField(
        null=True,
        blank=True,
        help_text='Ergebnis der KI-Validierung (complete, missing_data, etc.)',
    )

    # Metadaten
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Zusätzliche Workflow-Informationen',
    )

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    last_event_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'N8n Workflow Status'
        verbose_name_plural = 'N8n Workflow Status'

    def __str__(self):
        if self.precheck:
            return f"Workflow für Precheck #{self.precheck.id} - {self.get_status_display()}"
        elif self.quote:
            return f"Workflow für Quote #{self.quote.id} - {self.get_status_display()}"
        return f"Workflow {self.workflow_id} - {self.get_status_display()}"

    def update_status(self, new_status, metadata=None):
        """Status aktualisieren"""
        self.status = new_status
        self.last_event_at = timezone.now()

        if metadata:
            self.metadata.update(metadata)

        if new_status in ['quote_ready', 'sent_to_customer', 'failed']:
            self.completed_at = timezone.now()

        self.save()
