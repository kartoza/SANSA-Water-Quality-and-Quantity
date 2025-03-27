import os
import json
from django.test import TestCase
from django_project.core.settings.utils import absolute_path
from project.utils.calculations.pollution import PollutionAnalyzer


TEST_DATA_PATH = absolute_path('project', 'tests', 'data')

class PollutionAnalyzerRealDataTest(TestCase):
    def setUp(self):
        self.ndti_raster = os.path.join(TEST_DATA_PATH, 'NDTI_2024_01.tif')
        self.ndci_raster = os.path.join(TEST_DATA_PATH, 'NDCI_2024_01.tif')
        self.point_sources = os.path.join(TEST_DATA_PATH, 'point_sources.shp')
        self.non_point_sources = os.path.join(TEST_DATA_PATH, 'non_point_sources.shp')
        self.output_dir = os.path.join(TEST_DATA_PATH, 'test_reports')

        os.makedirs(self.output_dir, exist_ok=True)

    def test_generate_reports_with_real_data(self):
        analyzer = PollutionAnalyzer(
            ndti_raster=self.ndti_raster,
            ndci_raster=self.ndci_raster,
            point_sources=self.point_sources,
            non_point_areas=self.non_point_sources,
            output_dir=self.output_dir
        )

        analyzer.generate_reports()

        point_report = os.path.join(self.output_dir, "point_source_pollution.json")
        non_point_report = os.path.join(self.output_dir, "non_point_source_pollution.json")

        self.assertTrue(os.path.exists(point_report))
        self.assertTrue(os.path.exists(non_point_report))

        with open(point_report) as f:
            point_data = json.load(f)

        with open(non_point_report) as f:
            non_point_data = json.load(f)

        self.assertGreater(len(point_data), 0, "No point sources found")
        self.assertGreater(len(non_point_data), 0, "No non-point sources found")

        self.assertIn("mean_index", point_data[0])
        self.assertIsInstance(point_data[0]["mean_index"], (float, type(None)))
