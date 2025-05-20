import pickle
import os
import uuid as uuid_lib
import numpy as np
import xarray as xr
import pandas as pd
from core.settings.utils import absolute_path
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.conf import settings
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from core.factories import UserFactory  # Assuming this is your factory import
from project.models.monitor import AnalysisTask
from project.utils.calculations.analysis import Analysis


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class WaterAnalysisAPIViewTest(APITestCase):
    """Test WaterAnalysisAPIView and AnalysisTaskStatusAPIView.
    """
    fixtures = ["monitoring_indicator_type.json"]


    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(
            username=os.getenv("ADMIN_USERNAME", "admin"),
        )
        self.client.force_authenticate(user=self.user)

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

        payload = {
            "start_date":
            "2025-03-01",
            "end_date":
            "2025-03-31",
            "bbox":
            [19.0231, -33.9494, 19.0834, -33.9039],
            "calc_types": ["AWEI", "NDCI"],
            "export_cog": True,
            "export_plot": True,
            "export_nc": True,
        }

        # Trigger view POST
        url = reverse("water-analysis")
        response = self.client.post(url, payload, format="json")
        return response

    @patch("project.utils.calculations.analysis.Client")
    @patch("project.utils.calculations.analysis.stac_load")
    def test_creates_actual_file(self, mock_stac_load, mock_client):
        """
        Test that the view creates expected output files.
        """
        # Mock stac_load to return dummy xarray.Dataset with necessary bands
        response = self.setup_data(mock_stac_load, mock_client)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_id = response.data["task_uuid"]
        
        url = reverse("analysis-task-status", kwargs={"task_uuid": task_id})
        response = self.client.get(f"{url}?detail=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["task_name"], f"Water Analysis {self.user.username}")
        self.assertEqual(response.data["uuid"], str(task_id))
        self.assertEqual(response.data["status"], "SUCCESS")
        self.assertEqual(
            response.data["parameters"],
            {
                "bbox": [19.0231, -33.9494, 19.0834, -33.9039],
                "end_date": "2025-03-31",
                "export_nc": True,
                "calc_types": ["AWEI", "NDCI"],
                "export_cog": True,
                "resolution": 20,
                "start_date": "2025-03-01",
                "export_plot": True,
                "auto_detect_water": True,
                "mask_path": None,
            }
        )
        self.assertEqual(len(response.data["task_outputs"]), 6)
        awei_outputs = []
        ndci_outputs = []
        for output in response.data["task_outputs"]:
            if output["monitoring_type"] == "AWEI":
                awei_outputs.append(
                    output['file'].replace(
                        "http://testserver/media",
                        settings.MEDIA_ROOT
                    )
                )
            if output["monitoring_type"] == "NDCI":
                ndci_outputs.append(
                    output['file'].replace(
                        "http://testserver/media",
                        settings.MEDIA_ROOT
                    )
                )
        
        self.assertTrue(awei_outputs, 3)
        self.assertTrue(ndci_outputs, 3)
        for output in awei_outputs + ndci_outputs:
            self.assertTrue(os.path.exists(output))

    @patch("project.utils.calculations.analysis.Client")
    @patch("project.utils.calculations.analysis.stac_load")
    def test_no_duplicate_task(self, mock_stac_load, mock_client):
        """Test that AnalysisTask with same parameters will not be created twice.
        """

        # Before running analysis, no AnalysisTask should exist
        self.assertEqual(AnalysisTask.objects.count(), 0)        
        # Mock stac_load to return dummy xarray.Dataset with necessary bands
        response = self.setup_data(mock_stac_load, mock_client)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_id = response.data["task_uuid"]
        self.assertIsNotNone(task_id)
        
        # After running analysis, 1 AnalysisTask should be created
        self.assertEqual(AnalysisTask.objects.count(), 1)
        
        # After running analysis with same parameter, new AnalysisTask should NOT be created
        response = self.setup_data(mock_stac_load, mock_client)
        self.assertEqual(AnalysisTask.objects.count(), 1)
        self.assertEqual(response.data['status'], 'ready')
        self.assertEqual(
            response.data['output_url'], 
            'http://testserver/api/task-outputs/?monitoring_type__name__in=AWEI%2CNDCI&from_date=2025-03-01&to_date=2025-03-31&bbox=19.0231%2C-33.9494%2C19.0834%2C-33.9039'
        )
        self.assertIsNone(response.data['task_uuid'])
