from django.contrib import admin

from project.models.provider import Provider, DataSourceFile


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name', 'updated_at')


@admin.register(DataSourceFile)
class DataSourceFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'dataset', 'provider', 'uploaded_at')
    search_fields = ('name', 'uploaded_at')
