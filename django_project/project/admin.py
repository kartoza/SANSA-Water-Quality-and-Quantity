from django.contrib import admin

from project.models import (
    Provider, Dataset, DatasetType, DataSourceFile, 
    MonitoringIndicatorType, MonitoringIndicator, MonitoringReport, 
    APIUsageLog, ErrorLog, ScheduledTask, UserActivityLog, DataIngestionLog
)


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


@admin.register(DataSourceFile)
class DataSourceFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'dataset', 'provider', 'updated_at')
    search_fields = ('name', 'dataset__name', 'provider__name')
    list_filter = ('provider',)


@admin.register(MonitoringIndicatorType)
class MonitoringIndicatorTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(MonitoringIndicator)
class MonitoringIndicatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'dataset', 'monitoring_indicator_type', 'generated_at')
    search_fields = ('name', 'dataset__name')
    list_filter = ('monitoring_indicator_type',)


@admin.register(MonitoringReport)
class MonitoringReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'monitoring_indicator', 'generated_at')
    search_fields = ('monitoring_indicator__name', 'user__username')
    list_filter = ('generated_at',)


@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'endpoint', 'method', 'status_code', 'requested_at')
    search_fields = ('endpoint', 'user__username')
    list_filter = ('status_code', 'method')


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'module_name', 'error_type', 'error_message', 'occurred_at')
    search_fields = ('module_name', 'error_message')
    list_filter = ('occurred_at',)


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_name', 'status', 'started_at', 'completed_at')
    search_fields = ('task_name',)
    list_filter = ('status',)


@admin.register(DataIngestionLog)
class DataIngestionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_source_file', 'status', 'fetched_at')
    search_fields = ('data_source_file__name',)
    list_filter = ('status',)


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activity_type', 'timestamp')
    search_fields = ('user__username', 'activity_type')
    list_filter = ('timestamp',)
