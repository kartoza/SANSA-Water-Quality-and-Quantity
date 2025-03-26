from django.contrib import admin

from project.models.monitor import (
    MonitoringIndicator, 
    MonitoringIndicatorType, 
    MonitoringReport, 
    ScheduledTask,
    AnalysisTask,
    TaskOutput
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
    list_display = ('uuid', 'task_name', 'status' , 'started_at', 'completed_at')
    search_fields = ('name',)
    list_filter = ('status', 'started_at', 'completed_at')


class TaskOutputInline(admin.TabularInline):
    model = TaskOutput
    extra = 0
    fields = ('file', 'monitoring_type', 'created_at', 'created_by')
    readonly_fields = ('created_at',)
    show_change_link = True


@admin.register(AnalysisTask)
class AnalysisTaskAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'status', 'created_by', 'created_at', 'started_at', 'completed_at')
    list_filter = ('status', 'created_at', 'started_at', 'completed_at')
    search_fields = ('task_name', 'created_by__username')
    readonly_fields = ('uuid', 'started_at', 'created_at', 'completed_at')
    inlines = [TaskOutputInline]
    ordering = ('-created_at',)


@admin.register(TaskOutput)
class TaskOutputAdmin(admin.ModelAdmin):
    list_display = ('task', 'monitoring_type', 'file', 'created_by', 'created_at')
    list_filter = ('monitoring_type', 'created_by')
    search_fields = ('task__task_name', 'monitoring_type__name', 'created_by__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
