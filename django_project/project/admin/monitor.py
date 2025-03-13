from django.contrib import admin

from project.models.monitor import (
    MonitoringIndicator, 
    MonitoringIndicatorType, 
    MonitoringReport, 
    ScheduledTask
)

@admin.register(MonitoringIndicatorType)
class MonitoringIndicatorTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'monitoring_indicator_type')
    search_fields = ('name',)
    list_filter = ('monitoring_indicator_type',)


@admin.register(MonitoringIndicator)
class MonitoringIndicatorAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'dataset', 'monitoring_indicator_type', 
        'indicator_name', 'value', 'generated_at')
    search_fields = ('indicator_name',)
    list_filter = ('monitoring_indicator_type', 'generated_at')


@admin.register(MonitoringReport)
class MonitoringReportAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'monitoring_indicator', 
        'description', 'generated_at', 'report_link')
    search_fields = ('description', 'generated_at')


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_name', 'status' , 'started_at', 'completed_at')
    search_fields = ('name',)
    list_filter = ('status', 'started_at', 'completed_at')
