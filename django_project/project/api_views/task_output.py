from rest_framework import viewsets
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
