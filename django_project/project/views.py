from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import (
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
)
from celery.result import AsyncResult
from project.tasks import compute_water_extent_task, generate_water_mask_task


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

    def get(self, request):
        """
        API Endpoint to trigger water surface area calculation.
        """
        try:
            spatial_resolution = int(
                request.query_params.get("spatial_resolution", 30)
            )
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")
            bbox = request.query_params.get("bbox")
            input_type = request.query_params.get("input_type", "Landsat")

            if bbox:
                bbox = bbox.split(",")
                bbox = [float(coord) for coord in bbox]
            bbox_message = "Invalid bounding box format."
            if len(bbox) != 4:
                return Response(
                    {"status": "error", "message": bbox_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Convert bbox to float
            bbox = [float(coord) for coord in bbox]

            # Send task to Celery
            task = compute_water_extent_task.delay(
                bbox, spatial_resolution, start_date, end_date, input_type
            )

            return Response(
                {"status": "pending", "task_id": task.id},
                status=status.HTTP_202_ACCEPTED,
            )

        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class WaterExtentStatusView(APIView):
    """
    API to check the status of an async Water Extent Calculation.
    """

    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        """
        Check the status of a Celery task.
        """
        task_result = AsyncResult(task_id)

        if task_result.state == "SUCCESS":
            return Response(
                {"status": "completed", "data": task_result.result},
                status=status.HTTP_200_OK,
            )

        elif task_result.state == "PENDING":
            return Response(
                {"status": "pending"}, status=status.HTTP_202_ACCEPTED
            )

        elif task_result.state == "FAILURE":
            return Response(
                {"status": "failed", "message": str(task_result.result)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "unknown"}, status=status.HTTP_400_BAD_REQUEST
        )


class AWEIWaterMaskView(APIView):
    """
    API to generate the Water Mask asynchronously.
    """

    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        API Endpoint to trigger water mask generation.
        """
        try:
            spatial_resolution = int(
                request.query_params.get("spatial_resolution", 30)
            )
            bbox = request.query_params.get("bbox")
            input_type = request.query_params.get("input_type", "Landsat")

            if bbox:
                bbox = bbox.split(",")
                bbox = [float(coord) for coord in bbox]

            bbox = [float(coord) for coord in bbox]

            # Send task to Celery
            task = generate_water_mask_task.delay(
                bbox, spatial_resolution, input_type
            )

            return Response(
                {"status": "pending", "task_id": task.id},
                status=status.HTTP_202_ACCEPTED,
            )

        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class WaterMaskStatusView(APIView):
    """
    API to check the status of an async Water Mask generation.
    """

    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        """
        Check the status of a Celery task for water mask generation.
        """
        task_result = AsyncResult(task_id)

        if task_result.state == "SUCCESS":
            return Response(
                {"status": "completed", "data": task_result.result},
                status=status.HTTP_200_OK,
            )

        elif task_result.state == "PENDING":
            return Response(
                {"status": "pending"}, status=status.HTTP_202_ACCEPTED
            )

        elif task_result.state == "FAILURE":
            return Response(
                {"status": "failed", "message": str(task_result.result)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "unknown"}, status=status.HTTP_400_BAD_REQUEST
        )
