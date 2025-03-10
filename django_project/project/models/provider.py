from django.db import models


class Provider(models.Model):
    """
    Stores information about data providers.
    """
    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
