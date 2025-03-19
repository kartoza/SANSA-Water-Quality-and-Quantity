from django.urls import path
from project.api_views.analysis import WaterAnalysisView

urlpatterns = [
    path('water-analysis/', WaterAnalysisView.as_view(), name="water-analysis"),
]
