from django.db import models
from .api_logs import APIUsageLog
from .data_source import DataSourceFile


class DataIngestionLog(models.Model):
    """
    Stores data ingestion process logs.
    """

    api_log = models.ForeignKey(
        APIUsageLog, null=False, blank=False, on_delete=models.CASCADE
    )
    data_source_file = models.ForeignKey(
        DataSourceFile, null=False, blank=False, on_delete=models.CASCADE
    )
    description = models.TextField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    status = models.TextField()
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Ingestion Log {self.id}"
