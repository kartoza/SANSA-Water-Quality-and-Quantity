import json
from urllib.parse import urlencode
from django.shortcuts import get_object_or_404
from django.contrib.gis.geos import Polygon
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.authentication import (
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
)

from celery.result import AsyncResult
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from project.utils.calculations.analysis import Analysis
from project.models.monitor import MonitoringIndicatorType, AnalysisTask, TaskOutput
from project.tasks.analysis import run_analysis_task, run_analysis
from project.serializers.monitoring import AnalysisTaskStatusSerializer
from project.api_views.base import BasePaginationClass


class WaterAnalysisAPIView(APIView):
    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data

        # Mandatory fields
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        bbox = data.get("bbox")

        if not start_date or not end_date or not bbox:
            return Response(
                {"error": "start_date, end_date, and bbox are required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Optional fields with defaults
        resolution = data.get("resolution", 20)
        export_plot = data.get("export_plot", False)
        export_nc = data.get("export_nc", False)
        export_cog = data.get("export_cog", True)
        auto_detect_water = data.get("auto_detect_water", True)
        output_mask_id = data.get("output_mask_id")
        mask_path = None
        if output_mask_id:
            mask_path = get_object_or_404(TaskOutput, id=output_mask_id).file.path
        calc_types = data.get("calc_types", MonitoringIndicatorType.Type.values)
        for calc_type in calc_types:
            if calc_type not in MonitoringIndicatorType.Type.values:
                return Response(
                    {
                        "error":
                        f"{calc_type} is not one of available calculation type: "
                        f"['AWEI', 'NDCI', 'NDTI', 'SABI', 'CDOM']."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        parameters = {
            "start_date": start_date,
            "end_date": end_date,
            "bbox": bbox,
            "resolution": resolution,
            "export_plot": export_plot,
            "export_nc": export_nc,
            "export_cog": export_cog,
            "calc_types": calc_types,
            "auto_detect_water": auto_detect_water,
            "mask_path": mask_path
        }
        normalized_parameters = json.loads(json.dumps(parameters, sort_keys=True))

        # Check for existing TaskOutput
        existing_outputs = TaskOutput.objects.filter(
            monitoring_type__name__in=calc_types,
            bbox__intersects=Polygon.from_bbox(bbox),
            observation_date__gte=start_date,
            observation_date__lte=end_date,
        )
        output_url = request.build_absolute_uri(reverse('task-output-list'))
        query_params = {
            'monitoring_type__name__in': ','.join(calc_types),
            'from_date': start_date,
            'to_date': end_date,
            'bbox': ','.join([str(coord) for coord in bbox]),
        }
        absolute_url = f"{output_url}?{urlencode(query_params)}"
        if existing_outputs.exists():
            return Response({
                "status": "ready",
                "output_url": absolute_url,
                "task_uuid": None
            })

        task = AnalysisTask.objects.filter(
            parameters=normalized_parameters
        ).order_by('-created_at').first()

        if task:
            return Response(
                {"message": {
                    "task_uuid": task.uuid
                }},
                status=status.HTTP_200_OK,
            )
        else:
            task = AnalysisTask.objects.create(
                parameters=normalized_parameters,
                task_name=f"Water Analysis {self.request.user.username}",
                created_by=self.request.user,
            )
        parameters.update({"task_id": task.uuid.hex})

        try:
            result = run_analysis_task.delay(**parameters)
            task.refresh_from_db()
            task.celery_task_id = result.id
            task.save()

            return Response(
                {
                    "status": "processing",
                    "output_url": absolute_url,
                    "task_uuid": task.uuid
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            task.failed()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AnalysisTaskStatusAPIView(APIView):
    """
    API View to check the status of a Celery task.
    """
    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_uuid):
        detail = request.GET.get('detail', 'false').lower() in ['true', '1']
        task = get_object_or_404(AnalysisTask, uuid=task_uuid)
        if detail:
            serializer = AnalysisTaskStatusSerializer(task, context={'request': request})
            response = serializer.data
        else:
            response = {'status': serializer.data['status']}
        return Response(response, status=status.HTTP_200_OK)


class AnalysisTaskListAPIView(viewsets.ReadOnlyModelViewSet):
    """
    API View list AnalysisTask.
    """
    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = AnalysisTaskStatusSerializer
    pagination_class = BasePaginationClass
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = AnalysisTask.objects.all()
        if not self.request.user.is_superuser:
            return AnalysisTask.objects.filter(created_by=self.request.user)
        return queryset
