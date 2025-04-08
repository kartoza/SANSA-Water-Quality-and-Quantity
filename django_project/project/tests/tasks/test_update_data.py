import os
import datetime
import pickle
import uuid as uuid_lib
import numpy as np
import xarray as xr
import pandas as pd
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from core.factories import UserFactory
from core.settings.utils import absolute_path
from project.models.monitor import AnalysisTask, TaskOutput
from project.utils.calculations.analysis import Analysis
from project.tests.factories.monitor import CrawlerFactory
from project.tasks.store_data import update_stored_data


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestUpdateData(APITestCase):
    """Test Update Data task.
    """
    fixtures = ["monitoring_indicator_type.json"]

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(
            username=os.getenv("ADMIN_USERNAME", "admin"),
        )
        self.crawler = CrawlerFactory()
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

    @patch("project.utils.calculations.analysis.Client")
    @patch("project.utils.calculations.analysis.stac_load")
    def test_run_update_data(self, mock_stac_load, mock_client):
        """
        Test that the update data creates expected output files (AWEI, NDCI, NDTI).
        """
        # Mock stac_load to return dummy xarray.Dataset with necessary bands
        tz_now = timezone.now().replace(year=2025, month=4, day=2)
        with patch("project.tasks.store_data.timezone.now") as mock_tz_now:
            mock_tz_now.return_value = tz_now
            response = self.setup_data(mock_stac_load, mock_client)
            update_stored_data()

        outputs = TaskOutput.objects.all()

        # 3 Outputs are created
        self.assertEqual(outputs.count(), 3)

        # Outputs should have AWEI, NDCI, and NDTI type
        self.assertEqual(
            sorted(list(outputs.values_list('monitoring_type__name', flat=True))), 
            ['AWEI', 'NDCI', 'NDTI']
        )

        # Observation date should be 2025-03-01
        self.assertEqual(
            set(outputs.values_list('observation_date', flat=True)), 
            {datetime.date(2025, 3, 1)}
        )
