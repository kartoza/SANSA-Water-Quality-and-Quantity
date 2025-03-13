from django.db import models
from django.utils.translation import gettext_lazy as _


class DatasetType(models.Model):
    """
    Defines the type of dataset (e.g., Satellite, In-Situ).
    """
    class Type(models.TextChoices):
        SATELLITE = 'satellite', _('Satellite')
        IN_SITU = 'in-situ', _('In-Situ')

    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    dataset_type = models.CharField(
        choices=Type.choices,
        null=True,
        blank=True,
        max_length=25,
    )

    def __str__(self):
        return self.name


class Dataset(models.Model):
    """
    Stores structured datasets derived from raw data files.
    """
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    
    dataset_type = models.ForeignKey(
        DatasetType,
        on_delete=models.CASCADE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
