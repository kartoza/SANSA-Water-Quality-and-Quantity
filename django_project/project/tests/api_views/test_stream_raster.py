import os
import shutil
from datetime import date
from django.conf import settings
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from django.test import override_settings
from django.conf import settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from project.models.monitor import TaskOutput, MonitoringIndicatorType
from project.serializers.monitoring import TaskOutputSerializer
from core.settings.utils import absolute_path


class TaskOutputAPITestCase(APITestCase):
    """
    Test suite for the Task Output API endpoints including raster streaming.
    """

    fixtures = ["monitoring_indicator_type.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user(username="testuser", password="testpassword")
        cls.monitoring_type = MonitoringIndicatorType.objects.get(name="AWEI")
        cls.file_path = absolute_path("project/tests/data/SA_AWEI_2025-03.tif")
        mosaics_dir = os.path.join(
            settings.MEDIA_ROOT,
            'mosaics',
            'AWEI',
            '2025',
            '03'
        )
        if not os.path.exists(mosaics_dir):
            os.makedirs(mosaics_dir)
        cls.new_file_path = os.path.join(
            settings.MEDIA_ROOT,
            'mosaics',
            'AWEI',
            '2025',
            '03',
            'SA_AWEI_2025-03.tif'
        )
        shutil.copy(
            cls.file_path,
            cls.new_file_path
        )
        cls.task_output = TaskOutput.objects.create(
            monitoring_type=cls.monitoring_type,
            observation_date=date(2025, 3, 1),
            is_mosaic=True,
            file=cls.new_file_path
        )

    def setUp(self):
        """Create a test user and obtain a token for authentication."""
        super().setUp()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_task_output_list_authenticated(self):
        """Test that authenticated users can access task output list."""
        response = self.client.get("/api/task-outputs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_task_output_list_unauthenticated(self):
        """Test that unauthenticated users cannot access task output list."""
        self.client.credentials()  # Remove authentication
        response = self.client.get("/api/task-outputs/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_raster_stream_invalid_year(self):
        """Test error response for invalid year parameter."""
        response = self.client.get("/api/task-outputs/streams/AWEI/1800/03/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_raster_stream_invalid_month(self):
        """Test error response for invalid month parameter."""
        response = self.client.get("/api/task-outputs/streams/AWEI/2025/13/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_raster_stream_unauthenticated(self):
        """Test that unauthenticated users cannot access raster stream."""
        self.client.credentials()  # Remove authentication
        response = self.client.get("/api/task-outputs/streams/AWEI/2025/03/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_raster_stream_file_not_found(self):
        """Test error response when raster file doesn't exist."""
        response = self.client.get("/api/task-outputs/streams/AWEI/2023/01/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_raster_stream_success(self):
        """Test successful raster file streaming using real test file."""
        # Use the actual test file        
        response = self.client.get("/api/task-outputs/streams/AWEI/2025/03/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/tiff')
        self.assertEqual(response['Accept-Ranges'], 'bytes')
        self.assertIn('attachment; filename="SA_AWEI_2025-03.tif"', response['Content-Disposition'])
        
        # Verify file size header matches actual file
        actual_file_size = os.path.getsize(self.file_path)
        self.assertEqual(response['Content-Length'], str(actual_file_size))

    @patch('project.api_views.task_output.RasterStreamAPIView.get_raster_file_path')
    def test_raster_stream_different_indicator_types(self, mock_get_path):
        """Test raster streaming with different indicator types."""
        mock_get_path.return_value = self.file_path
        
        # Test different indicator types
        indicator_types = ['NDVI', 'EVI', 'AWEI']
        
        for indicator_type in indicator_types:
            response = self.client.get(f"/api/task-outputs/streams/{indicator_type}/2025/03/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(f'SA_{indicator_type}_2025-03.tif', response['Content-Disposition'])

    def test_raster_stream_lowercase_indicator_type(self):
        """Test that lowercase indicator types are converted to uppercase."""
        
        response = self.client.get("/api/task-outputs/streams/awei/2025/03/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('SA_AWEI_2025-03.tif', response['Content-Disposition'])

    def test_raster_stream_content_streaming(self):
        """Test that file content is properly streamed."""
        
        response = self.client.get("/api/task-outputs/streams/AWEI/2025/03/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response is streaming
        self.assertTrue(hasattr(response, 'streaming_content'))
        
        # Read the streamed content and verify it matches the file
        streamed_content = b''.join(response.streaming_content)
        
        with open(self.file_path, 'rb') as f:
            actual_content = f.read()
        
        self.assertEqual(len(streamed_content), len(actual_content))
        self.assertEqual(streamed_content, actual_content)

    def test_raster_stream_edge_case_dates(self):
        """Test edge cases for year and month validation."""
        # Test minimum valid year (should fail because file doesn't exist)
        response = self.client.get("/api/task-outputs/streams/AWEI/1900/01/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test maximum valid year (should fail because file doesn't exist)
        response = self.client.get("/api/task-outputs/streams/AWEI/2100/12/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test invalid years
        response = self.client.get("/api/task-outputs/streams/AWEI/1899/01/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response = self.client.get("/api/task-outputs/streams/AWEI/2101/01/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test invalid months
        response = self.client.get("/api/task-outputs/streams/AWEI/2025/00/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_raster_file_path_construction(self):
        """Test that the file path is constructed correctly."""
        from project.api_views.task_output import RasterStreamAPIView
        
        view = RasterStreamAPIView()
        file_path = view.get_raster_file_path('AWEI', 2025, 3)
        
        expected_path = os.path.join(
            settings.MEDIA_ROOT,
            'mosaics',
            'AWEI',
            '2025',
            '03',
            'SA_AWEI_2025-03.tif'
        )
        
        self.assertEqual(file_path, expected_path)

    def test_raster_stream_cache_headers(self):
        """Test that appropriate cache headers are set."""
        
        response = self.client.get("/api/task-outputs/streams/AWEI/2025/03/")
        
        # Check cache control header is set (from @method_decorator)
        self.assertIn('Cache-Control', response)
        self.assertIn('max-age=3600', response['Cache-Control'])

    def test_raster_stream_chunk_iteration(self):
        """Test that file is read in chunks for streaming."""
        
        from project.api_views.task_output import RasterStreamAPIView
        view = RasterStreamAPIView()
        
        # Test file iterator with small chunk size
        chunks = list(view.file_iterator(self.file_path, chunk_size=1024))
        
        # Verify we got multiple chunks for a reasonably sized file
        self.assertGreater(len(chunks), 0)
        
        # Verify total content matches file
        total_content = b''.join(chunks)
        with open(self.file_path, 'rb') as f:
            actual_content = f.read()
        
        self.assertEqual(total_content, actual_content)

    def test_raster_stream_file_iterator_nonexistent_file(self):
        """Test file iterator with non-existent file raises Http404."""
        from project.api_views.task_output import RasterStreamAPIView
        from django.http import Http404
        
        view = RasterStreamAPIView()
        
        with self.assertRaises(Http404):
            list(view.file_iterator("/nonexistent/file.tif"))

    def test_combined_raster_info(self):
        """Test combined raster info is returned correctly."""
        
        response = self.client.get("/api/task-outputs/awei/2025/03/")

        serializer = TaskOutputSerializer(self.task_output)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'file_stream': 'http://testserver/api/task-outputs/streams/awei/2025/3/', 
                'id': self.task_output.id, 
                'task_id': None, 
                'file': 'http://testserver/media/home/web/media/mosaics/AWEI/2025/03/SA_AWEI_2025-03.tif', 
                'size': 0, 
                'monitoring_type': 'AWEI', 
                'created_at': serializer.data['created_at'],
                'observation_date': '2025-03-01', 
                'period': 'monthly'
            }
        )