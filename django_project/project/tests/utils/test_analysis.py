import os
import tempfile
import xarray as xr
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from django.test import TestCase
from project.utils.calculations.analysis import Analysis
from project.models import MonitoringIndicatorType


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

        # Override the default export path inside the CalculateMonitoring to use tmpdir
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = Analysis(
                start_date="2024-02-01",
                end_date="2024-02-29",
                bbox=[-10, -10, 10, 10]
            )

            # Patch export dir logic (assuming your class uses something like f"/tmp/{uuid4()}")
            calc.output_dir = os.path.join(tmpdir, str(mock_uuid.return_value))

            # Make sure export dir exists for saving
            os.makedirs(calc.output_dir, exist_ok=True)

            calc.run()


            for val in MonitoringIndicatorType.Type.values:
                # ✅ Assert files exist inside mocked UUID dir
                self.assertTrue(os.path.exists(os.path.join(calc.output_dir, f"{val}_2024_01.png")))
                self.assertTrue(os.path.exists(os.path.join(calc.output_dir, f"{val}_2024_01.nc")))
                self.assertTrue(os.path.exists(os.path.join(calc.output_dir, f"{val}_2024_01.tif")))
