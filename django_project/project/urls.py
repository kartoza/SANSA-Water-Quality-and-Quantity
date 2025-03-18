from django.urls import path
from project.api_views.analysis import WaterAnalysisAPIView, AnalysisTaskStatusAPIView
from project.views.dataset import DatasetOverviewView
from project.views import AWEIWaterExtentView, AWEIWaterMaskView

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
        "awei-water-mask/",
        AWEIWaterMaskView.as_view(),
        name="awei-water-mask"
    ),
]
