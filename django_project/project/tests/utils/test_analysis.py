import pickle
import os
import tempfile
import xarray as xr
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from core.settings.utils import absolute_path
from django.test import TestCase
from project.utils.calculations.analysis import Analysis
from project.models import MonitoringIndicatorType, AnalysisTask, TaskOutput


class AnalysisFileGenerationTest(TestCase):

    fixtures = ["monitoring_indicator_type.json"]

    @patch("project.utils.calculations.analysis.uuid.uuid4")
    @patch("project.utils.calculations.analysis.Client")
    @patch("project.utils.calculations.analysis.stac_load")
    def test_files_are_generated(self, mock_stac_load, mock_client, mock_uuid):
        # Mock UUID
        mock_uuid.return_value = "12345678-1234-5678-1234-567812345678"

        # Mock STAC and data
        mock_search = MagicMock()
        mock_search.items.return_value = [MagicMock()] * 5
        mock_client.open.return_value.search.return_value = mock_search
        dummy_data = None
        pickle_file_path = absolute_path("project/tests/data/analysis/dataset.pkl")
        with open(pickle_file_path, "rb") as f:
            dummy_data = pickle.load(f)

        mock_stac_load.return_value = dummy_data
        task = AnalysisTask.objects.create()

        # Override the default export path inside the CalculateMonitoring to use tmpdir
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = Analysis(
                start_date="2025-03-01",
                end_date="2025-03-31",
                bbox=[
                    19.0718146707764333, 
                    -34.1046576825389707, 
                    19.3240754498619083, 
                    -33.9548456688371942
                ],
                export_cog=True,
                export_plot=True,
                export_nc=True,
                task=task,
                calc_types=['AWEI', 'NDTI', 'NDCI'],

            )
        
            # Patch export dir logic (assuming your class uses something like f"/tmp/{uuid4()}")
            calc.output_dir = os.path.join(tmpdir, str(mock_uuid.return_value))
        
            # Make sure export dir exists for saving
            os.makedirs(calc.output_dir, exist_ok=True)
        
            calc.run()

            for output in TaskOutput.objects.all():
                self.assertTrue(os.path.exists(output.file.path))
