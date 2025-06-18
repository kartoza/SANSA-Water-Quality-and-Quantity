import os
import mimetypes
from django.shortcuts import reverse
from django.http import StreamingHttpResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.conf import settings
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
)
from rest_framework import permissions
from django_filters.rest_framework import DjangoFilterBackend
from project.models.monitor import TaskOutput
from project.serializers.monitoring import TaskOutputSerializer
from project.filters.task_output import TaskOutputFilter
from project.api_views.base import BasePaginationClass


class TaskOutputViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    queryset = TaskOutput.objects.all().order_by('-created_at')
    serializer_class = TaskOutputSerializer
    pagination_class = BasePaginationClass
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskOutputFilter

    def get_mosaic_output(self, request, indicator_type, year, month):
        """
        Handle GET request for mosaic task outputs with specific indicator_type, year, and month
        """
        try:
            task_output = TaskOutput.objects.get(
                is_mosaic=True,
                monitoring_type__name__iexact=indicator_type,
                observation_date__year=year,
                observation_date__month=month
            )
        except TaskOutput.DoesNotExist:
            return Response(
                {'error': 'TaskOutput not found with the specified criteria'},
                status=404
            )
        except TaskOutput.MultipleObjectsReturned:
            task_output = TaskOutput.objects.filter(
                is_mosaic=True,
                monitoring_type__name__iexact=indicator_type,
                observation_date__year=year,
                observation_date__month=month
            ).order_by('-created_at').first()
        serializer = self.get_serializer(task_output)
        data = {
            'file_stream': request.build_absolute_uri(
                reverse('raster-stream', args=[indicator_type, year, month])
            )
        }
        data.update(serializer.data)
        return Response(data)


class RasterStreamAPIView(APIView):
    """
    Stream raster file content based on year and month parameters
    """

    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get_raster_file_path(self, indicator_type, year, month):
        """
        Construct the file path for the raster file based on indicator
        type, year and month
        """
        task_output = TaskOutput.objects.filter(
            is_mosaic=True,
            monitoring_type__name__iexact=indicator_type,
            observation_date__year=year,
            observation_date__month=month
        ).order_by('-created_at').first()
        if task_output:
            return task_output.file.path
        else:
            filename = f"SA_{indicator_type}_{year}-{month:02d}.tif"
            file_path = os.path.join(
                settings.MEDIA_ROOT,
                'mosaics',
                indicator_type,
                str(year),
                f"{month:02d}",
                filename
            )
            return file_path

    def file_iterator(self, file_path, chunk_size=8192):
        """
        Generator to read file in chunks for streaming
        """
        try:
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except IOError:
            raise Http404("Raster file not found")

    @method_decorator(cache_control(max_age=3600))  # Cache for 1 hour
    def get(self, request, *args, **kwargs):
        # Get year and month from URL parameters or query parameters
        indicator_type = kwargs.get('indicator_type') or request.GET.get('indicator_type')
        indicator_type = indicator_type.upper()
        year = kwargs.get('year') or request.GET.get('year')
        month = kwargs.get('month') or request.GET.get('month')

        # Validate parameters
        if not year or not month:
            raise Http404("Year and month parameters are required")

        try:
            year = int(year)
            month = int(month)

            # Validate ranges
            if not (1900 <= year <= 2100):
                raise ValueError("Invalid year")
            if not (1 <= month <= 12):
                raise ValueError("Invalid month")

        except (ValueError, TypeError):
            raise Http404("Invalid year or month format")

        # Get file path
        file_path = self.get_raster_file_path(indicator_type, year, month)

        # Check if file exists
        if not os.path.exists(file_path):
            raise Http404(f"Raster file for {indicator_type} {year}-{month:02d} not found")

        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        # Get file size for Content-Length header
        file_size = os.path.getsize(file_path)

        # Create streaming response
        response = StreamingHttpResponse(
            self.file_iterator(file_path),
            content_type=content_type
        )

        # Set headers
        response['Content-Length'] = str(file_size)
        response['Content-Disposition'] = (
            f'attachment; filename="SA_{indicator_type}_{year}-{month:02d}.tif"'
        )
        response['Accept-Ranges'] = 'bytes'

        return response
