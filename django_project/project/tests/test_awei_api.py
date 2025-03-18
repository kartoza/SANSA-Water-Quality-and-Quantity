from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from unittest.mock import patch


class AWEIApiTestCase(APITestCase):
    """
    Test suite for the AWEI Water Extent & Water Mask API endpoints.
    """

    def setUp(self):
        """Create a test user and obtain a token for authentication."""
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
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

    @patch("project.tasks.compute_water_extent_task.delay")
    def test_trigger_awei_water_extent_task(self, mock_task):
        """Test if the water extent task is triggered successfully."""
        mock_task.return_value.id = "mock-task-id"

        response = self.client.get(
            "/api/awei-water-extent/", self.valid_payload
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("task_id", response.data)
        self.assertEqual(response.data["status"], "pending")

    @patch("project.tasks.generate_water_mask_task.delay")
    def test_trigger_awei_water_mask_task(self, mock_task):
        """Test if the water mask task is triggered successfully."""
        mock_task.return_value.id = "mock-task-id"

        response = self.client.get("/api/awei-water-mask/", self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("task_id", response.data)
        self.assertEqual(response.data["status"], "pending")

    # **Validation Tests**

    def test_awei_water_extent_invalid_bbox(self):
        """Test error response for invalid bounding box."""
        response = self.client.get(
            "/api/awei-water-extent/", self.invalid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    def test_awei_water_mask_invalid_bbox(self):
        """Test error response for invalid bounding box."""
        response = self.client.get(
            "/api/awei-water-mask/", self.invalid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    # **Task Status Checks - Water Extent**

    @patch("celery.result.AsyncResult")
    def test_check_water_extent_status_completed(self, mock_async_result):
        """Test checking the status of a completed water extent task."""
        mock_async_result.return_value.state = "SUCCESS"
        mock_async_result.return_value.result = {"area_km2": 500}

        response = self.client.get(
            "/api/awei-water-extent/status/mock-task-id/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
        self.assertIn("data", response.data)

    @patch("celery.result.AsyncResult")
    def test_check_water_extent_status_pending(self, mock_async_result):
        """Test checking the status of a pending water extent task."""
        mock_async_result.return_value.state = "PENDING"

        response = self.client.get(
            "/api/awei-water-extent/status/mock-task-id/"
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["status"], "pending")

    @patch("celery.result.AsyncResult")
    def test_check_water_extent_status_failed(self, mock_async_result):
        """Test checking the status of a failed water extent task."""
        mock_async_result.return_value.state = "FAILURE"
        mock_async_result.return_value.result = "Error message"

        response = self.client.get(
            "/api/awei-water-extent/status/mock-task-id/"
        )

        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertEqual(response.data["status"], "failed")

    # **Task Status Checks - Water Mask**

    @patch("celery.result.AsyncResult")
    def test_check_water_mask_status_completed(self, mock_async_result):
        """Test checking the status of a completed water mask task."""
        mock_async_result.return_value.state = "SUCCESS"
        mock_async_result.return_value.result = {
            "mask_url": "http://example.com/mask.tif"
        }

        response = self.client.get(
            "/api/awei-water-mask/status/mock-task-id/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
        self.assertIn("data", response.data)

    @patch("celery.result.AsyncResult")
    def test_check_water_mask_status_pending(self, mock_async_result):
        """Test checking the status of a pending water mask task."""
        mock_async_result.return_value.state = "PENDING"

        response = self.client.get(
            "/api/awei-water-mask/status/mock-task-id/"
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["status"], "pending")

    @patch("celery.result.AsyncResult")
    def test_check_water_mask_status_failed(self, mock_async_result):
        """Test checking the status of a failed water mask task."""
        mock_async_result.return_value.state = "FAILURE"
        mock_async_result.return_value.result = "Error message"

        response = self.client.get(
            "/api/awei-water-mask/status/mock-task-id/"
        )

        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertEqual(response.data["status"], "failed")
