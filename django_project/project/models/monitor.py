import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from project.models.dataset import Dataset

User = get_user_model()


class MonitoringIndicatorType(models.Model):
    """
    Defines types of monitoring indicators.
    """
    class Type(models.TextChoices):
        AWEI = 'AWEI', _('AWEI')
        NDTI = 'NDTI', _('NDTI')
        NDCI = 'NDCI', _('NDCI')
        SABI = 'SABI', _('SABI')
        CDOM = 'CDOM', _('CDOM')
    
    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    
    monitoring_indicator_type = models.CharField(
        choices=[],
        null=True,
        blank=True,
        max_length=25,
    )

    def __str__(self):
        return f"Monitoring Indicator Type {self.name}"


class MonitoringIndicator(models.Model):
    """
    Stores monitoring indicators for datasets.
    """
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE
    )
    monitoring_indicator_type = models.ForeignKey(
        MonitoringIndicatorType,
        on_delete=models.CASCADE
    )
    indicator_name  = models.CharField(
        max_length=100
    )
    value = models.FloatField(null=True, blank=False)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Monitoring Indicator {self.id} - {self.indicator_name}"


class MonitoringReport(models.Model):
    """
    Stores generated reports on water quality.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    monitoring_indicator = models.ForeignKey(
        MonitoringIndicator,
        on_delete=models.CASCADE
    )
    description = models.TextField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now=True)
    report_link = models.URLField()

    def __str__(self):
        return f"Report {self.id} - {self.monitoring_indicator.name}"


class ScheduledTask(models.Model):
    """
    Tracks scheduled background jobs.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        RUNNING = 'running', _('Running')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')

    uuid = models.UUIDField(
        default=uuid.uuid4, 
        editable=False,
        primary_key=True
    )

    task_name = models.CharField(
        null=False,
        blank=False,
        max_length=100
    )
    status = models.CharField(
        choices=Status.choices,
        null=False,
        blank=False,
        max_length=25,
        default=Status.PENDING
    )
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.task_name
