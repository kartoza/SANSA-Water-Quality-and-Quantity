from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from unittest.mock import patch

from project.models import AnalysisTask


class AWEIApiTestCase(APITestCase):
    """
    Test suite for the AWEI Water Extent & Water Mask API endpoints.
    """

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

    # **Triggering Tasks Tests**

    @patch("project.tasks.water_extent.compute_water_extent_task.delay")
    def test_trigger_awei_water_extent_task(self, mock_task):
        """Test if the water extent task is triggered successfully."""
        mock_task.return_value.id = self.uuid

        response = self.client.post("/api/awei-water-extent/", self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("task_uuid", response.data['message'])

    @patch("project.tasks.water_extent.generate_water_mask_task.delay")
    def test_trigger_awei_water_mask_task(self, mock_task):
        """Test if the water mask task is triggered successfully."""
        mock_task.return_value.id = self.uuid

        response = self.client.post("/api/awei-water-mask/", self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("task_uuid", response.data['message'])

    # **Validation Tests**

    def test_awei_water_extent_invalid_bbox(self):
        """Test error response for invalid bounding box."""
        response = self.client.post("/api/awei-water-extent/", self.invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_awei_water_mask_invalid_bbox(self):
        """Test error response for invalid bounding box."""
        response = self.client.post("/api/awei-water-mask/", self.invalid_payload)
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

    # **Task Status Checks - Water Mask**

    @patch("project.api_views.water_extent.AsyncResult")
    def test_check_water_mask_status_completed(self, mock_async_result):
        """Test checking the status of a completed water mask task."""
        mock_async_result.return_value.status = "SUCCESS"
        mock_async_result.return_value.result = {"mask_url": "http://example.com/mask.tif"}

        response = self.client.get("/api/awei-water-mask/12345678-1234-5678-1234-567812345678/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "SUCCESS")

    @patch("project.api_views.water_extent.AsyncResult")
    def test_check_water_mask_status_pending(self, mock_async_result):
        """Test checking the status of a pending water mask task."""
        mock_async_result.return_value.status = "PENDING"

        response = self.client.get("/api/awei-water-mask/12345678-1234-5678-1234-567812345678/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "PENDING")

    @patch("project.api_views.water_extent.AsyncResult")
    def test_check_water_mask_status_failed(self, mock_async_result):
        """Test checking the status of a failed water mask task."""
        mock_async_result.return_value.status = "FAILURE"
        mock_async_result.return_value.result = "Error message"

        response = self.client.get("/api/awei-water-mask/12345678-1234-5678-1234-567812345678/")

        self.assertEqual(response.data["status"], "FAILURE")
