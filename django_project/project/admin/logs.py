from django.contrib import admin

from project.models.logs import (
    APIUsageLog, 
    DataIngestionLog, 
    ErrorLog,
    UserActivityLog
)


@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'endpoint', 'method', 'status_code', 'requested_at')
    search_fields = ('endpoint',)
    list_filter = ('method',)


@admin.register(DataIngestionLog)
class DataIngestionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'api_log', 'data_source', 'fetched_at', 'status', 'message')
    search_fields = ('data_source', 'message')
    list_filter = ('status',)


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'api_log', 'task', 'module_name', 'error_type', 'error_message', 'occured_at')
    search_fields = ('error_message',)
    list_filter = ('error_type',)


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activity_type', 'timestamp')
    search_fields = ('user__username',)
    list_filter = ('activity_type',)