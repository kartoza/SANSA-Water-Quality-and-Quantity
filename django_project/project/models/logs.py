from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from project.models.provider import DataSourceFile
from project.models.monitor import ScheduledTask

User = get_user_model()


class APIUsageLog(models.Model):
    """
    Tracks API request history.
    """
    class Method(models.TextChoices):
        GET = 'GET', _('GET')
        POST = 'POST', _('POST')
        PUT = 'PUT', _('PUT')
        DELETE = 'DELETE', _('DELETE')

    user = models.ForeignKey(
        User,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )
    endpoint = models.TextField()
    method = models.CharField(
        choices=Method.choices,
        max_length=10
    )    
    status_code = models.IntegerField()
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"API Log {self.id} - {self.endpoint}"


class DataIngestionLog(models.Model):
    """
    Logs data ingestion attempts.
    """
    class Status(models.TextChoices):
        SUCCESS = 'success', _('Success')
        FAILED = 'failed', _('Failed')

    api_log = models.ForeignKey(
        APIUsageLog,
        on_delete=models.CASCADE
    )
    data_source_file = models.ForeignKey(
        DataSourceFile,
        on_delete=models.CASCADE
    )
    fetched_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        choices=Status.choices,
        max_length=25
    )
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Ingestion Log {self.id}"


class ErrorLog(models.Model):
    """
    Captures errors in the system.
    """
    api_log = models.ForeignKey(
        APIUsageLog,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    task = models.ForeignKey(
        ScheduledTask,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    module_name = models.CharField(
        null=False,
        blank=False,
        max_length=100
    )
    error_type = models.CharField(
        null=False,
        blank=False,
        max_length=100
    )
    error_message = models.TextField()
    occured_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Error {self.id} - {self.module_name}"


class UserActivityLog(models.Model):
    """
    Tracks user activities (logins, downloads, updates, etc.).
    """
    class ActivityType(models.TextChoices):
        LOGIN = 'LOGIN', _('LOGIN')
        LOGOUT = 'LOGOUT', _('LOGOUT')
        DOWNLOAD = 'DOWNLOAD', _('DOWNLOAD')
        UPDATE = 'UPDATE', _('UPDATE')
        DELETE = 'DELETE', _('DELETE')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    activity_type = models.CharField(
        choices=ActivityType.choices,
        max_length=25
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.user.username} - {self.activity_type}"