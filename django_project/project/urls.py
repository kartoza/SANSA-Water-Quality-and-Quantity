from django.urls import path
from project.api_views.analysis import WaterAnalysisAPIView, AnalysisTaskStatusAPIView
from project.api_views.dataset import DatasetOverviewView

urlpatterns = [
    path('datasets/', DatasetOverviewView.as_view(), name="datasets-overview"),
    path('water-analysis/', WaterAnalysisAPIView.as_view(), name="water-analysis"),
    path('analysis-task/<uuid:task_uuid>/', AnalysisTaskStatusAPIView.as_view(), name='analysis-task-status')
]
