from django.db import models
from django.contrib.auth.models import User
from .monitoring import MonitoringIndicator


class MonitoringReport(models.Model):
    """
    Reports generated from monitoring indicators.
    """

    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    monitoring_indicator = models.ForeignKey(
        MonitoringIndicator, null=False, blank=False, on_delete=models.CASCADE
    )
    description = models.TextField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    report_link = models.TextField()

    def __str__(self):
        return f"Report {self.id} - {self.monitoring_indicator.name}"
