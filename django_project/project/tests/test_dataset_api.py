from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from project.models import Dataset, DatasetType


class DatasetAPITestCase(TestCase):
    """
    This test case tests the API for the Dataset model.
    """

    def setUp(self):
        self.client = APIClient()

        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create authentication token
        self.token = Token.objects.create(user=self.user)

        # Create a test dataset type
        self.dataset_type = DatasetType.objects.create(
            name="Satellite", description="Satellite data"
        )

        # Create test datasets
        self.dataset1 = Dataset.objects.create(
            name="Test Dataset 1",
            description="First test dataset",
            dataset_type=self.dataset_type,
        )
        self.dataset2 = Dataset.objects.create(
            name="Test Dataset 2",
            description="Second test dataset",
            dataset_type=self.dataset_type,
        )

    def test_api_requires_authentication(self):
        """Test that API returns 401 Unauthorized when no token is provided"""
        response = self.client.get("/api/datasets/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_returns_dataset_list(self):
        """Test that API returns dataset list when authenticated"""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )  # Set token
        response = self.client.get("/api/datasets/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "total_entries", response.data["results"]
        )  # Ensure total_entries is returned
        self.assertEqual(response.data["results"]["total_entries"], 2)
