from django.urls import path
from project.api_views import (
    WaterAnalysisAPIView,
    AnalysisTaskStatusAPIView,
    AWEIWaterExtentView,
    WaterExtentStatusView,
    TaskOutputViewSet,
    AnalysisTaskListAPIView,
    RasterStreamAPIView
)
from project.api_views.dataset import (
    DatasetOverviewView, )

urlpatterns = [
    path('datasets/', DatasetOverviewView.as_view(), name="datasets-overview"),
    path('water-analysis/', WaterAnalysisAPIView.as_view(), name="water-analysis"),
    path('water-analysis/<uuid:task_uuid>/',
         AnalysisTaskStatusAPIView.as_view(),
         name='analysis-task-status'),
    path(
        "awei-water-extent/<uuid:task_uuid>/",
        WaterExtentStatusView.as_view(),
        name="water-extent-status",
    ),
    path("awei-water-extent/", AWEIWaterExtentView.as_view(), name="awei-water-extent"),
    path(
        'task-outputs/<str:indicator_type>/<int:year>/<int:month>/',
        RasterStreamAPIView.as_view(),
        name='raster-stream'
    ),
    path("task-outputs/", TaskOutputViewSet.as_view({'get': 'list'}), name="task-output-list"),
    path(
        "analysis-tasks/",
        AnalysisTaskListAPIView.as_view({'get': 'list'}),
        name="analysis-tasks-list"
    ),
]
