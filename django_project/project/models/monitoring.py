from django.db import models
from .dataset import Dataset


class MonitoringIndicatorType(models.Model):
    """
    Defines the types of monitoring indicators.
    """

    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class MonitoringIndicator(models.Model):
    """
    Stores monitoring indicators for water quality and quantity.
    """

    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    dataset = models.ForeignKey(
        Dataset, null=False, blank=False, on_delete=models.CASCADE
    )
    monitoring_indicator_type = models.ForeignKey(
        MonitoringIndicatorType, null=False, blank=False, on_delete=models.CASCADE
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
