from django.db import models
from .api_logs import APIUsageLog
from .scheduled_tasks import ScheduledTask


class ErrorLog(models.Model):
    """
    Stores error logs linked to API usage or scheduled tasks.
    """

    api_log = models.ForeignKey(
        APIUsageLog, null=False, blank=False, on_delete=models.CASCADE
    )
    task = models.ForeignKey(
        ScheduledTask, null=True, blank=True, on_delete=models.CASCADE
    )
    module_name = models.TextField()
    error_type = models.TextField()
    error_message = models.TextField()
    occurred_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Error {self.id} - {self.module_name}"
