from django.db import models
from django.contrib.auth.models import User


class UserActivityLog(models.Model):
    """
    Logs user activities within the system.
    """

    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    activity_type = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.user.username} - {self.activity_type}"
