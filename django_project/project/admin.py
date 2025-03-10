from django.contrib import admin

from project.models.provider import Provider
from project.models.dataset import Dataset, DatasetType


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)


@admin.register(DatasetType)
class DatasetTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'dataset_type', 
        'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('dataset_type',)

