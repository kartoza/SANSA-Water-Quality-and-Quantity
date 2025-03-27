from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import (
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
)
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Min, Max
from .models import Dataset, DatasetType
from .serializers import DatasetSerializer
from celery.result import AsyncResult
from project.tasks import compute_water_extent_task, generate_water_mask_task


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

    def get(self, request, task_id):
        """
        Check the status of a Celery task.
        """
        task_result = AsyncResult(task_id)

        if task_result.state == "SUCCESS":
            return Response(
                {
                    "status": "completed",
                    "data": task_result.result
                },
                status=status.HTTP_200_OK,
            )

        elif task_result.state == "PENDING":
            return Response({"status": "pending"}, status=status.HTTP_202_ACCEPTED)

        elif task_result.state == "FAILURE":
            return Response(
                {
                    "status": "failed",
                    "message": str(task_result.result)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"status": "unknown"}, status=status.HTTP_400_BAD_REQUEST)


class DatasetOverviewView(APIView, PageNumberPagination):
    """
    Returns a summary of all stored datasets, including total records,
    categories, and metadata.
    Supports pagination.
    """

    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    page_size = 10

    def get(self, request):
        queryset = Dataset.objects.select_related("dataset_type").all()
        dataset_type = request.query_params.get("dataset_type", None)

        if dataset_type:
            queryset = queryset.filter(dataset_type__name=dataset_type)

        total_entries = queryset.count()
        categories = DatasetType.objects.values("name").annotate(count=Count("dataset"))
        metadata = queryset.aggregate(
            min_date=Min("created_at"),
            max_date=Max("created_at"),
        )

        # Paginate results
        paginated_queryset = self.paginate_queryset(queryset, request, view=self)
        serialized_data = DatasetSerializer(paginated_queryset, many=True).data

        return self.get_paginated_response({
            "total_entries": total_entries,
            "data_categories": list(categories),
            "metadata": metadata,
            "datasets": serialized_data,
        })


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
        try:
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

            # Send task to Celery
            task = compute_water_extent_task.delay(bbox, spatial_resolution, start_date, end_date,
                                                   input_type)

            return Response(
                {
                    "status": "pending",
                    "task_id": task.id
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except ValueError as e:
            return Response(
                {
                    "status": "error",
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class WaterExtentStatusView(BaseTaskStatusView):
    """
    API to check the status of an async Water Extent Calculation.
    """
    pass


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

    def post(self, request):
        """
        API Endpoint to trigger water mask generation.
        """
        try:
            spatial_resolution = int(request.data.get("spatial_resolution", 30))
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

            # Send task to Celery
            task = generate_water_mask_task.delay(bbox, spatial_resolution, input_type)

            return Response(
                {
                    "status": "pending",
                    "task_id": task.id
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except ValueError as e:
            return Response(
                {
                    "status": "error",
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class WaterMaskStatusView(BaseTaskStatusView):
    """
    API to check the status of an async Water Mask generation.
    """
    pass
