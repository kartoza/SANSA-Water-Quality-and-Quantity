from django.urls import path
from project.api_views import (
    WaterAnalysisAPIView,
    AnalysisTaskStatusAPIView,
    AWEIWaterExtentView,
    WaterExtentStatusView,
    AWEIWaterMaskView,
    WaterMaskStatusView,
)
from project.api_views.dataset import (
    DatasetOverviewView,
)

urlpatterns = [
    path('datasets/', 
         DatasetOverviewView.as_view(), 
         name="datasets-overview"),
    path('water-analysis/', 
         WaterAnalysisAPIView.as_view(), 
         name="water-analysis"),
    path('water-analysis/<uuid:task_uuid>/', 
         AnalysisTaskStatusAPIView.as_view(), 
         name='analysis-task-status'),
    path(
        "awei-water-extent/<uuid:task_uuid>/",
        WaterExtentStatusView.as_view(),
        name="water-extent-status",
    ),
    path(
        "awei-water-extent/",
        AWEIWaterExtentView.as_view(),
        name="awei-water-extent"
    ),
    path(
        "awei-water-mask/<uuid:task_uuid>/",
        WaterMaskStatusView.as_view(),
        name="water-mask-status",
    ),
    path(
        "awei-water-mask/",
        AWEIWaterMaskView.as_view(),
        name="awei-water-mask"
    ),
]
