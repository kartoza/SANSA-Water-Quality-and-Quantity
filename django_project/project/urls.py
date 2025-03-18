from django.urls import path
from project.api_views.analysis import WaterAnalysisAPIView, AnalysisTaskStatusAPIView
from project.views.dataset import DatasetOverviewView
from .views import (
    AWEIWaterExtentView,
    WaterExtentStatusView,
    AWEIWaterMaskView,
    WaterMaskStatusView,
)

urlpatterns = [
    path('datasets/', DatasetOverviewView.as_view(), name="datasets-overview"),
    path('water-analysis/', WaterAnalysisAPIView.as_view(), name="water-analysis"),
    path('analysis-task/<uuid:task_uuid>/', AnalysisTaskStatusAPIView.as_view(), name='analysis-task-status'),
    path(
        "awei-water-extent/",
        AWEIWaterExtentView.as_view(),
        name="awei-water-extent"
    ),
    path(
        "awei-water-extent/status/<str:task_id>/",
        WaterExtentStatusView.as_view(),
        name="water-extent-status",
    ),
    path(
        "awei-water-mask/",
        AWEIWaterMaskView.as_view(),
        name="awei-water-mask"
    ),
    path(
        "awei-water-mask/status/<str:task_id>/",
        WaterMaskStatusView.as_view(),
        name="water-mask-status",
    ),
]
