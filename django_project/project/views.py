from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Min, Max
from .models import Dataset, DatasetType
from .serializers import DatasetSerializer


class DatasetOverviewView(APIView, PageNumberPagination):
    """
    Returns a summary of all stored datasets, including total records,
    categories, and metadata.
    Supports pagination.
    """

    permission_classes = [permissions.IsAuthenticated]
    page_size = 10

    def get(self, request):
        queryset = Dataset.objects.select_related("dataset_type").all()
        dataset_type = request.query_params.get("dataset_type", None)

        if dataset_type:
            queryset = queryset.filter(dataset_type__name=dataset_type)

        total_entries = queryset.count()
        categories = DatasetType.objects.values(
            "name").annotate(count=Count("dataset"))
        metadata = queryset.aggregate(
            min_date=Min("created_at"),
            max_date=Max("created_at"),
        )

        # Paginate results
        paginated_queryset = self.paginate_queryset(
            queryset, request, view=self
        )
        serialized_data = DatasetSerializer(paginated_queryset, many=True).data

        return self.get_paginated_response(
            {
                "total_entries": total_entries,
                "data_categories": list(categories),
                "metadata": metadata,
                "datasets": serialized_data,
            }
        )
