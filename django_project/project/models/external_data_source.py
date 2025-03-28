from django.db import models


class ExternalDataSource(models.Model):
    """
    Stores configurations for dynamically managed external data sources.
    """

    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    description = models.TextField(null=True, blank=True)
    api_url = models.URLField(null=False, blank=False, help_text="API Endpoint URL")
    requires_auth = models.BooleanField(default=False,
                                        help_text="If true, authentication is required")
    auth_token = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="API authentication token (if required)",
    )
    request_method = models.CharField(
        max_length=10,
        choices=[("GET", "GET"), ("POST", "POST")],
        default="GET",
        help_text="HTTP request method for the API",
    )
    response_format = models.CharField(
        max_length=10,
        choices=[
            ("JSON", "JSON"),
            ("XML", "XML"),
            ("CSV", "CSV"),
            ("GeoTIFF", "GeoTIFF"),
        ],
        default="JSON",
        help_text="Format of the response data",
    )
    additional_params = models.JSONField(null=True,
                                         blank=True,
                                         help_text="Extra parameters for API calls")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
