import logging
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from project.models.dataset import Dataset

User = get_user_model()


class MonitoringIndicatorType(models.Model):
    """
    Defines types of monitoring indicators.
    """

    class Type(models.TextChoices):
        AWEI = 'AWEI', _('AWEI')
        AWEI_MASK = 'AWEI_MASK', _('AWEI_MASK')
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
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    monitoring_indicator_type = models.ForeignKey(MonitoringIndicatorType, on_delete=models.CASCADE)
    indicator_name = models.CharField(max_length=100)
    value = models.FloatField(null=True, blank=False)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Monitoring Indicator {self.id} - {self.indicator_name}"


class MonitoringReport(models.Model):
    """
    Stores generated reports on water quality.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    monitoring_indicator = models.ForeignKey(MonitoringIndicator, on_delete=models.CASCADE)
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

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    task_name = models.CharField(null=False, blank=False, max_length=100)
    status = models.CharField(choices=Status.choices,
                              null=False,
                              blank=False,
                              max_length=25,
                              default=Status.PENDING)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.task_name


class AnalysisTask(models.Model):
    """
    Tracks analysis tasks.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        RUNNING = 'running', _('Running')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    task_name = models.CharField(null=False, blank=False, max_length=100)
    status = models.CharField(choices=Status.choices,
                              null=False,
                              blank=False,
                              max_length=25,
                              default=Status.PENDING)
    parameters = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    celery_task_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.task_name

    def start(self):
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save()

    def complete(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def failed(self):
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.save()

    def add_log(self, log, level=logging.INFO):
        from project.models.logs import TaskLog

        task_log = TaskLog(
            content_object=self,
            log=log,
            level=level,
        )
        task_log.save()


def output_layer_dir_path(instance, filename):
    """Return upload directory path for Output Layer."""
    file_path = f'{str(instance.created_by.pk)}/{str(instance.task.uuid)}/'
    file_path = file_path + filename
    return file_path


class TaskOutput(models.Model):
    """Output of a task.
    """

    task = models.ForeignKey(AnalysisTask, related_name='task_outputs', on_delete=models.CASCADE)

    file = models.FileField(upload_to=output_layer_dir_path)
    size = models.BigIntegerField(default=0)
    monitoring_type = models.ForeignKey(MonitoringIndicatorType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
