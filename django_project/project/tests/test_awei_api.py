import uuid
import os
import pickle
import uuid as uuid_lib
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import xarray as xr
from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django_celery_results.models import TaskResult
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from core.factories import UserFactory
from core.settings.utils import absolute_path
from project.models import AnalysisTask
from project.models.monitor import AnalysisTask  # Check if this is needed, it's a duplicate import
from project.utils.calculations.analysis import Analysis


class AWEIApiTestCase(APITestCase):
    """
    Test suite for the AWEI Water Extent & Water Mask API endpoints.
    """
    fixtures = ["monitoring_indicator_type.json"]

    def setUp(self):
        """Create a test user and obtain a token for authentication."""
        self.uuid = '12345678-1234-5678-1234-567812345678'
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        AnalysisTask.objects.create(
            uuid=self.uuid,
            created_by=self.user,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.valid_bbox = "102.0,0.5,103.0,1.5"
        self.invalid_bbox = "invalid,values"

        self.valid_payload = {
            "spatial_resolution": 30,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "bbox": self.valid_bbox,
            "input_type": "Landsat",
        }

        self.invalid_payload = {
            "spatial_resolution": 30,
            "start_date": "2024-01-01",
            "end_date": "invalid-date",
            "bbox": self.invalid_bbox,
            "input_type": "Landsat",
        }
        TaskResult.objects.all().delete()

    def setup_data(self, mock_stac_load, mock_client):
        """Setup dummy data for processing.
        """

        mock_search = MagicMock()
        mock_search.items.return_value = [MagicMock()] * 5
        mock_client.open.return_value.search.return_value = mock_search
        dummy_data = None
        pickle_file_path = absolute_path("project/tests/data/analysis/dataset.pkl")
        with open(pickle_file_path, "rb") as f:
            dummy_data = pickle.load(f)

        mock_stac_load.return_value = dummy_data

    # **Triggering Tasks Tests**
    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_TASK_STORE_EAGER_RESULT=True
    )
    @patch("project.utils.calculations.analysis.Client")
    @patch("project.utils.calculations.analysis.stac_load")
    @patch("project.api_views.water_extent.AsyncResult")
    def test_aaaaa(self, mock_async_result, mock_stac_load, mock_client):
        """Test if the water extent task is triggered successfully."""
        # Mock stac_load to return dummy xarray.Dataset with necessary bands
        mock_async_result.return_value.status = "SUCCESS"
        mock_async_result.return_value.result = {"area_km2": 4.78}
        response = self.setup_data(mock_stac_load, mock_client)
        response = self.client.post("/api/awei-water-extent/", self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("task_uuid", response.data['message'])
        
        task_uuid = response.data['message']['task_uuid']
        # check status
        response = self.client.get(f"/api/awei-water-extent/{task_uuid}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['area_km2'], 4.78)


    # **Validation Tests**
    def test_awei_water_extent_invalid_bbox(self):
        """Test error response for invalid bounding box."""
        response = self.client.post("/api/awei-water-extent/", self.invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    # **Task Status Checks - Water Extent**
    @patch("project.api_views.water_extent.AsyncResult")
    def test_check_water_extent_status_completed(self, mock_async_result):
        """Test checking the status of a completed water extent task."""
        mock_async_result.return_value.status = "SUCCESS"
        mock_async_result.return_value.result = {"area_km2": 500}

        response = self.client.get("/api/awei-water-extent/12345678-1234-5678-1234-567812345678/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "SUCCESS")

    @patch("project.api_views.water_extent.AsyncResult")
    def test_check_water_extent_status_pending(self, mock_async_result):
        """Test checking the status of a pending water extent task."""
        mock_async_result.return_value.status = "PENDING"

        response = self.client.get("/api/awei-water-extent/12345678-1234-5678-1234-567812345678/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "PENDING")

    @patch("project.api_views.water_extent.AsyncResult")
    def test_check_water_extent_status_failed(self, mock_async_result):
        """Test checking the status of a failed water extent task."""
        mock_async_result.return_value.status = "FAILURE"
        mock_async_result.return_value.result = "Error message"

        response = self.client.get("/api/awei-water-extent/12345678-1234-5678-1234-567812345678/")

        self.assertEqual(response.data["status"], "FAILURE")
