from django.db import models


class DatasetType(models.Model):
    """
    Defines the type of dataset (e.g., Satellite, In-Situ).
    """
    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)


class Dataset(models.Model):
    """
    Stores structured datasets derived from raw data files.
    """
    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    
    dataset_type = models.ForeignKey(
        DatasetType,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
