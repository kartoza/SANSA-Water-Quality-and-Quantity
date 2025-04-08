from django.contrib import admin

from project.models.logs import (APIUsageLog, DataIngestionLog, ErrorLog, UserActivityLog, TaskLog)


@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'endpoint', 'method', 'status_code', 'requested_at')
    search_fields = ('endpoint', )
    list_filter = ('method', 'requested_at')


@admin.register(DataIngestionLog)
class DataIngestionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'api_log', 'data_source_file', 'fetched_at', 'status', 'message')
    search_fields = ('data_source_file', 'message')
    list_filter = ('status', 'fetched_at')


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'api_log', 'task', 'module_name', 'error_type', 'error_message',
                    'occured_at')
    search_fields = ('error_message', )
    list_filter = ('error_type', 'occured_at')


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activity_type', 'timestamp')
    search_fields = ('user__username', )
    list_filter = ('activity_type', 'timestamp')


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'log', 'level', 'timestamp', 'content_type', 'object_id')
    search_fields = ('uuid', 'log', 'object_id')
    list_filter = ('level', 'timestamp', 'content_type')
    ordering = ('-timestamp', )
