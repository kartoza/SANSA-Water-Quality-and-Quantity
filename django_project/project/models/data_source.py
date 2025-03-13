from django.db import models
from .dataset import Dataset
from .provider import Provider


class DataSourceFile(models.Model):
    """
    Represents raw data sources associated with datasets and providers.
    """

    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    dataset = models.ForeignKey(
        Dataset, null=False, blank=False, on_delete=models.CASCADE
    )
    provider = models.ForeignKey(
        Provider, null=False, blank=False, on_delete=models.CASCADE
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
