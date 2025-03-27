from django.contrib import admin
from project.models import ExternalDataSource


@admin.register(ExternalDataSource)
class ExternalDataSourceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "api_url", "requires_auth", "created_at")
    search_fields = ("name", "api_url")
    list_filter = ("requires_auth", )
    fieldsets = (
        ("General Information", {
            "fields": ("name", "description")
        }),
        (
            "API Configuration",
            {
                "fields": (
                    "api_url",
                    "requires_auth",
                    "auth_token",
                    "request_method",
                    "response_format",
                    "additional_params",
                ),
                "classes": ("collapse", ),
            },
        ),
    )
