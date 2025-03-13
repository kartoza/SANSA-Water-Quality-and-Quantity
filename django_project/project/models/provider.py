from django.db import models
from project.models.dataset import Dataset


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


class DataSourceFile(models.Model):
    """
    Stores information about raw data files received from providers.
    """
    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    
    dataset = models.ForeignKey(
        Dataset,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )
    provider = models.ForeignKey(
        Provider,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )
    
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
