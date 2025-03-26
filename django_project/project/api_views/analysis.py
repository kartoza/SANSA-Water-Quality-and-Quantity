import json
from django.shortcuts import get_object_or_404
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
from project.models.monitor import MonitoringIndicatorType, AnalysisTask
from project.tasks.analysis import run_analysis
from project.serializers.monitoring import AnalysisTaskStatusSerializer


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
        export_plot = data.get("export_plot", True)
        export_nc = data.get("export_nc", True)
        export_cog = data.get("export_cog", True)
        calc_types = data.get("calc_types", MonitoringIndicatorType.Type.values)  # Can be None
        for calc_type in calc_types:
            if calc_type not in MonitoringIndicatorType.Type.values:
                return Response(
                    {"error": f"{calc_type} is not one of available calculation type: ['AWEI', 'NDCI', 'NDTI', 'SABI', 'CDOM']."}, 
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
        }
        normalized_parameters = json.loads(json.dumps(parameters, sort_keys=True))
        try:
            task, created = AnalysisTask.objects.get_or_create(
                parameters=normalized_parameters,
                defaults={
                    "task_name": f"Water Analysis {self.request.user.username}",
                    "created_by": self.request.user,
                }
            )
        except AnalysisTask.MultipleObjectsReturned:
            task = AnalysisTask.objects.filter(
                parameters=parameters
            ).order_by('-created_at').first()
            created = False
        if not created:
            return Response(
                {"message": {"task_uuid": task.uuid}},
                status=status.HTTP_200_OK,
            )
        parameters.update({"task_id": task.uuid.hex})

        try:
            result = run_analysis.delay(**parameters)
            task.celery_task_id = result.id
            task.save()

            return Response(
                {"message": {"task_uuid": task.uuid}},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            task.failed()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AnalysisTaskStatusAPIView(APIView):
    def get(self, request, task_uuid):
        task = get_object_or_404(AnalysisTask, uuid=task_uuid)
        result = AsyncResult(task.celery_task_id)
        serializer = AnalysisTaskStatusSerializer(task, context={'request': request})
        
        response = serializer.data
        response['status'] = result.status
        return Response(response, status=status.HTTP_200_OK)
