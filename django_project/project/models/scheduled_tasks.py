from django.db import models


class ScheduledTask(models.Model):
    """
    Logs scheduled task execution details.
    """

    task_name = models.TextField()
    status = models.TextField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.task_name
