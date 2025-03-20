from django.urls import path
from project.api_views.analysis import WaterAnalysisView, AnalysisTaskStatusView

urlpatterns = [
    path('datasets/', DatasetOverviewView.as_view(), name="datasets-overview"),
    path('water-analysis/', WaterAnalysisView.as_view(), name="water-analysis"),
    path('analysis-task/<uuid:uuid>/', AnalysisTaskStatusView.as_view(), name='analysis-task-status')
]
