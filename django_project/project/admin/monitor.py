from leaflet.admin import LeafletGeoAdmin
from django.contrib import admin
from django.contrib import messages

from project.models.monitor import (
    MonitoringIndicator,
    MonitoringIndicatorType,
    MonitoringReport,
    ScheduledTask,
    AnalysisTask,
    TaskOutput,
    Crawler,
    CrawlProgress,
    Province
)
from project.tasks.store_data import update_stored_data


@admin.register(MonitoringIndicatorType)
class MonitoringIndicatorTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'monitoring_indicator_type')
    search_fields = ('name', )
    list_filter = ('monitoring_indicator_type', )


@admin.register(MonitoringIndicator)
class MonitoringIndicatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'dataset', 'monitoring_indicator_type', 'indicator_name', 'value',
                    'generated_at')
    search_fields = ('indicator_name', )
    list_filter = ('monitoring_indicator_type', 'generated_at')


@admin.register(MonitoringReport)
class MonitoringReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'monitoring_indicator', 'description', 'generated_at',
                    'report_link')
    search_fields = ('description', 'generated_at')


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'task_name', 'status', 'started_at', 'completed_at')
    search_fields = ('name', )
    list_filter = ('status', 'started_at', 'completed_at')


class TaskOutputInline(admin.TabularInline):
    model = TaskOutput
    extra = 0
    fields = ('file', 'monitoring_type', 'created_at', 'created_by')
    readonly_fields = ('created_at', )
    show_change_link = True


@admin.register(AnalysisTask)
class AnalysisTaskAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'status', 'created_by', 'created_at', 'started_at', 'completed_at')
    list_filter = ('status', 'created_at', 'started_at', 'completed_at')
    search_fields = ('task_name', 'created_by__username', 'uuid', 'celery_task_id')
    readonly_fields = ('uuid', 'started_at', 'created_at', 'completed_at')
    inlines = [TaskOutputInline]
    ordering = ('-created_at', )


@admin.register(TaskOutput)
class TaskOutputAdmin(LeafletGeoAdmin):
    list_display = ('task', 'monitoring_type', 'file', 'size', 'created_by', 'created_at')
    list_filter = ('monitoring_type', 'created_by')
    search_fields = ('task__task_name', 'monitoring_type__name', 'created_by__username')
    readonly_fields = ('created_at', )
    ordering = ('-created_at', )


@admin.action(description="Run crawler for last month")
def run_crawler(modeladmin, request, queryset):
    update_stored_data(list(queryset.values_list('id', flat=True)))
    message = f"Running {queryset.count()} selected crawlers."
    messages.info(request, message)


@admin.register(Crawler)
class CrawlerAdmin(LeafletGeoAdmin):
    list_display = ('name', 'description', 'image_type', 'created_at', 'created_by')
    list_filter = ('image_type', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('updated_by', 'created_by')
    actions = [run_crawler]

    def save_model(self, request, obj, form, change):
        if not obj.created_by:  # Only set if it's a new object
            obj.created_by = request.user
        obj.updated_by = request.user
        obj.save(validate=False)


@admin.register(CrawlProgress)
class CrawlProgressAdmin(admin.ModelAdmin):
    list_display = (
        'crawler', 'started_at', 'completed_at',
        'status', 'progress', 'data_to_process',
        'processed_data'
    )
    search_fields = ('crawler__name', 'status')
    list_filter = ('status', 'started_at', 'completed_at')


admin.site.register(Province)
