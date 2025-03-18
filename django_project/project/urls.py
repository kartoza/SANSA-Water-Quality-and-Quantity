from django.urls import path
from .views import AWEIWaterExtentView, AWEIWaterMaskView

urlpatterns = [
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
