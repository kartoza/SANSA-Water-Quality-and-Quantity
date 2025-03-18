from django.urls import path
from .views import DatasetOverviewView

urlpatterns = [
    path('datasets/', DatasetOverviewView.as_view(), name="datasets-overview"),
]
