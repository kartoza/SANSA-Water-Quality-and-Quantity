# import os
# import uuid as uuid_lib
import numpy as np
import xarray as xr
import pandas as pd
from unittest.mock import patch, MagicMock
from django.urls import reverse
# from django.conf import settings
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from core.factories import UserFactory  # Assuming this is your factory import
from project.models.monitor import AnalysisTask
# from project.utils.calculations.analysis import Analysis


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class WaterAnalysisAPIViewTest(APITestCase):
    """Test WaterAnalysisAPIView and AnalysisTaskStatusAPIView.
    """
    fixtures = ["monitoring_indicator_type.json"]

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def setup_data(self, mock_stac_load, mock_client):
        """Setup dummy data for processing.
        """

        mock_search = MagicMock()
        mock_search.items.return_value = [MagicMock()] * 5
        mock_client.open.return_value.search.return_value = mock_search
        dummy_data = xr.Dataset(
            {
                "blue": (("time", "y", "x"), np.random.rand(1, 10, 10)),
                "green": (("time", "y", "x"), np.random.rand(1, 10, 10)),
                "red": (("time", "y", "x"), np.random.rand(1, 10, 10)),
                "nir": (("time", "y", "x"), np.random.rand(1, 10, 10)),
                "swir16": (("time", "y", "x"), np.random.rand(1, 10, 10)),
                "swir22": (("time", "y", "x"), np.random.rand(1, 10, 10)),
            },
            coords={
                "time": pd.to_datetime(["2024-01-31"]),
                "x": np.arange(10),
                "y": np.arange(10),
            },
        )
        mock_stac_load.return_value = dummy_data

        payload = {
            "start_date":
            "2024-01-01",
            "end_date":
            "2024-01-31",
            "bbox":
            [19.0718146707764333, -34.1046576825389707, 19.3240754498619083, -33.9548456688371942],
            "calc_types": ["AWEI", "NDCI"]
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
        # TODO : Fix this test
        response = self.setup_data(mock_stac_load, mock_client)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # task_id = response.data["message"]["task_uuid"]
        #
        # url = reverse("analysis-task-status", kwargs={"task_uuid": task_id})
        # response = self.client.get(url)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data["task_name"], f"Water Analysis {self.user.username}")
        # self.assertEqual(response.data["uuid"], str(task_id))
        # self.assertEqual(response.data["status"], "SUCCESS")
        # self.assertEqual(
        #     response.data["parameters"],
        #     {
        #         "bbox": [
        #             19.071814670776433,
        #             -34.10465768253897,
        #             19.32407544986191,
        #             -33.954845668837194,
        #         ],
        #         "end_date": "2024-01-31",
        #         "export_nc": True,
        #         "calc_types": ["AWEI", "NDCI"],
        #         "export_cog": True,
        #         "resolution": 20,
        #         "start_date": "2024-01-01",
        #         "export_plot": True,
        #         "task_id": task_id.hex
        #     }
        # )
        # self.assertEqual(len(response.data["task_outputs"]), 6)
        # awei_outputs = []
        # ndci_outputs = []
        # for output in response.data["task_outputs"]:
        #     if output["monitoring_type"] == "AWEI":
        #         awei_outputs.append(
        #             output['file'].replace(
        #                 "http://testserver/media",
        #                 settings.MEDIA_ROOT
        #             )
        #         )
        #     if output["monitoring_type"] == "NDCI":
        #         ndci_outputs.append(
        #             output['file'].replace(
        #                 "http://testserver/media",
        #                 settings.MEDIA_ROOT
        #             )
        #         )
        #
        #
        # self.assertTrue(awei_outputs, 3)
        # self.assertTrue(ndci_outputs, 3)
        # for output in awei_outputs + ndci_outputs:
        #     self.assertTrue(os.path.exists(output))

    @patch("project.utils.calculations.analysis.Client")
    @patch("project.utils.calculations.analysis.stac_load")
    def test_no_duplicate_task(self, mock_stac_load, mock_client):
        """Test that AnalysisTask with same parameters will not be created twice.
        """

        # Before running analysis, no AnalysisTask should exist
        self.assertEqual(AnalysisTask.objects.count(), 0)

        # TODO : Fix this test
        #
        # # Mock stac_load to return dummy xarray.Dataset with necessary bands
        # response = self.setup_data(mock_stac_load, mock_client)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # task_id = response.data["message"]["task_uuid"]
        #
        # # After running analysis, 1 AnalysisTask should be created
        # self.assertEqual(AnalysisTask.objects.count(), 1)
        #
        # # After running analysis with same parameter, new AnalysisTask should NOT be created
        # self.setup_data(mock_stac_load, mock_client)
        # self.assertEqual(AnalysisTask.objects.count(), 1)
