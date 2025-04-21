import logging
import uuid

from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Polygon
from django.db.models import F
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from project.models.dataset import Dataset

User = get_user_model()


class Status(models.TextChoices):
    PENDING = 'pending', _('Pending')
    RUNNING = 'running', _('Running')
    COMPLETED = 'completed', _('Completed')
    FAILED = 'failed', _('Failed')


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
        return self.name


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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    celery_task_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.task_name

    def start(self):
        self.status = Status.RUNNING
        self.started_at = timezone.now()
        self.save()

    def complete(self):
        self.status = Status.COMPLETED
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
    if instance.created_by:
        file_path = f'{str(instance.created_by.pk)}/{str(instance.task.uuid)}/'
    else:
        file_path = f'0/{str(instance.task.uuid)}/'
    file_path = file_path + filename
    return file_path


class TaskOutput(models.Model):
    """Output of a task.
    """

    class AnalysisPeriod(models.TextChoices):
        DAILY = 'daily', _('Daily')
        MONTHLY = 'monthly', _('Monthly')

    task = models.ForeignKey(AnalysisTask, related_name='task_outputs', on_delete=models.CASCADE)
    file = models.FileField(upload_to=output_layer_dir_path)
    size = models.BigIntegerField(default=0)
    monitoring_type = models.ForeignKey(MonitoringIndicatorType, on_delete=models.CASCADE)
    period = models.CharField(
        max_length=10,
        choices=AnalysisPeriod.choices,
        default=AnalysisPeriod.MONTHLY,
    )
    observation_date = models.DateField(
        help_text="Date when the observation was taken",
        null=True,
        blank=True
    )
    bbox = models.PolygonField(null=True, blank=True, srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)


class Province(models.Model):
    """Stores information about provinces.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    bbox = models.PolygonField(null=True, blank=True, srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='provinces_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='provinces_updated'

    )

    def __str__(self):
        return self.name


class Crawler(models.Model):
    """Stores information about web crawlers.
    """
    class ImageType(models.TextChoices):
        LANDSAT = 'landsat', _('landsat')
        SENTINEL = 'sentinel', _('sentinel')

    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, null=True, blank=True)
    bbox = models.PolygonField(null=True, blank=True, srid=4326)
    image_type = models.CharField(
        choices=ImageType.choices,
        default=ImageType.SENTINEL,
    )
    resolution = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='crawler_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='crawler_updated_by',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self._validate_and_set_bbox()

    def save(self, *args, validate=True, **kwargs):
        if validate:
            self.full_clean()
        return super().save(*args, **kwargs)

    def _validate_and_set_bbox(self):
        """Validate and set province/bbox fields."""
        is_new = self._state.adding

        if is_new:
            if self.province and self.bbox:
                raise ValidationError(
                    "Only one of 'province' or 'bbox' should be set on creation."
                )
            elif self.province:
                self.bbox = self.province.bbox
            elif not self.bbox:
                raise ValidationError(
                    "You must set either 'province' or 'bbox' when creating a Crawler."
                )
        else:
            old = Crawler.objects.get(pk=self.pk)
            province_changed = self.province != old.province
            bbox_changed = self.bbox != old.bbox

            if province_changed and bbox_changed:
                raise ValidationError(
                    "Only one of 'province' or 'bbox' may be changed at a time."
                )
            elif province_changed:
                if self.province:
                    if self.bbox != self.province.bbox:
                        self.bbox = self.province.bbox
                else:
                    raise ValidationError(
                        "Cannot unset province without providing a bbox."
                    )


class CrawlProgress(models.Model):
    """
    Stores progress of a crawler.
    """

    crawler = models.ForeignKey(Crawler, on_delete=models.CASCADE)
    data_to_process = models.IntegerField(default=0)
    processed_data = models.IntegerField(default=0)
    progress = models.FloatField(default=0)
    status = models.CharField(max_length=20, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Crawl Progress for {self.crawler.name}"
    
    def increment_processed_data(self):
        # Increment processed_data by 1 using F expression
        CrawlProgress.objects.filter(pk=self.pk).update(processed_data=F('processed_data') + 1)

        # Refresh from DB to get the updated value
        self.refresh_from_db(fields=['processed_data', 'data_to_process'])

        # Recalculate progress
        if self.data_to_process > 0:
            self.progress = int((self.processed_data / self.data_to_process) * 100)

        if self.progress >= 100:
            self.status = Status.COMPLETED
            self.completed_at = timezone.now()

        # Save the updated progress
        self.save()
