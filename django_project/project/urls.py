from django.urls import path
from .views import (
    AWEIWaterExtentView,
    WaterExtentStatusView,
    AWEIWaterMaskView,
    WaterMaskStatusView,
)

urlpatterns = [
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
