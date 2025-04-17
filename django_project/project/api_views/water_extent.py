import json
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import (
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
)
from celery.result import AsyncResult
from project.models.monitor import AnalysisTask
from project.serializers.monitoring import AnalysisTaskStatusSerializer
from project.tasks.water_extent import (compute_water_extent_task, generate_water_mask_task)


class BaseTaskStatusView(APIView):
    """
    Base API View to check the status of a Celery task.
    """

    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_uuid):
        """
        Check the status of a Celery task.
        """
        task = get_object_or_404(AnalysisTask, uuid=task_uuid)
        result = AsyncResult(str(task.celery_task_id))
        serializer = AnalysisTaskStatusSerializer(task, context={'request': request})

        response = serializer.data
        response['status'] = result.status

        if result.status == "SUCCESS" and isinstance(result.result, dict):
            # Only inject known extra fields if present
            if "area_km2" in result.result:
                response["area_km2"] = result.result["area_km2"]

        return Response(response, status=status.HTTP_200_OK)


class AWEIWaterExtentView(APIView):
    """
    API to compute the Water Surface Area Extent asynchronously.
    """

    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        API Endpoint to trigger water surface area calculation.
        """
        spatial_resolution = int(request.data.get("spatial_resolution", 30))
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        bbox = request.data.get("bbox")
        input_type = request.data.get("input_type", "Landsat")

        if isinstance(bbox, str):
            bbox = bbox.split(",")
        try:
            bbox = [float(coord) for coord in bbox]
        except ValueError:
            bbox_message = "Invalid bounding box format."
            return Response(
                {
                    "status": "error",
                    "message": bbox_message
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build parameter dict
        parameters = {
            "bbox": bbox,
            "spatial_resolution": spatial_resolution,
            "start_date": start_date,
            "end_date": end_date,
            "input_type": input_type,
        }

        # Normalize parameter ordering to avoid duplicate mismatch
        normalized_parameters = json.loads(json.dumps(parameters, sort_keys=True))

        # Check if task with same parameters already exists
        try:
            task, created = AnalysisTask.objects.get_or_create(
                parameters=normalized_parameters,
                defaults={
                    "task_name": f"Water Extent - {request.user.username}",
                    "created_by": request.user,
                })
        except AnalysisTask.MultipleObjectsReturned:
            task = AnalysisTask.objects.filter(
                parameters=normalized_parameters).order_by('-created_at').first()
            created = False

        if not created:
            return Response(
                {
                    "message": {
                        "task_uuid": task.uuid
                    },
                },
                status=status.HTTP_200_OK,
            )

        # Trigger Celery task
        parameters.update({"task_id": str(task.uuid)})
        try:
            result = compute_water_extent_task.delay(**parameters)
            task.celery_task_id = result.id
            task.save()

            return Response(
                {"message": {
                    "task_uuid": task.uuid
                }},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            task.failed()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WaterExtentStatusView(BaseTaskStatusView):
    """
    API to check the status of an async Water Extent Calculation.
    """
    pass

