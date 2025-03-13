from django.db import models
from django.contrib.auth.models import User


class APIUsageLog(models.Model):
    """
    Logs API usage events.
    """

    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    endpoint = models.TextField()
    method = models.TextField()
    status_code = models.IntegerField()
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"API Log {self.id} - {self.endpoint}"
