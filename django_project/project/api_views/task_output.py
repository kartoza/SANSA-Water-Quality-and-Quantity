from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from project.models.monitor import TaskOutput
from project.serializers.monitoring import TaskOutputSerializer
from project.filters.task_output import TaskOutputFilter


class TaskOutputPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskOutputViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskOutput.objects.all().order_by('-created_at')
    serializer_class = TaskOutputSerializer
    pagination_class = TaskOutputPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskOutputFilter
