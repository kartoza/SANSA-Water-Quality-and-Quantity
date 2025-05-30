import uuid
import os
import datetime
import pickle
import uuid as uuid_lib
import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from unittest.mock import patch, MagicMock
from shapely.geometry import box
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from core.factories import UserFactory
from core.settings.utils import absolute_path
from project.models.monitor import AnalysisTask, TaskOutput, CrawlProgress, Status
from project.utils.calculations.analysis import Analysis
from project.tests.factories.monitor import CrawlerFactory
from project.tasks.store_data import update_stored_data, process_crawler


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

    def get_catchment_gdf(self, crawler):
        gdf = gpd.read_file(
            absolute_path('project', 'data', 'catchments.gpkg'),
            layer="catchments"
        )

        bbox = crawler.bbox.extent
        # Create a shapely box (rectangle geometry)
        bbox_geom = box(*bbox)
        filtered = gdf[gdf.geometry.within(bbox_geom)]
        return filtered

    def get_water_body_gdf(self, geom_to_intersect):
        gdf = gpd.read_file(
            absolute_path('project', 'data', 'sa_waterbodies.gpkg'),
            layer="waterbodies"
        )
        filtered = gdf[
            gdf.geometry.intersects(geom_to_intersect)
        ].sort_values(by="area_m2", ascending=False)
        return filtered

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_TASK_STORE_EAGER_RESULT=True
    )
    @patch("project.tasks.store_data.process_water_body.delay")
    def test_process_water_body_call_count(self, mock_process_water_body):
        """Test that process_water_body is called as the amount of waterbody"""
        def side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.id = uuid.uuid4()
            return mock_result
        mock_process_water_body.side_effect = side_effect
        process_crawler(
            datetime.date(2025, 4, 1),
            datetime.date(2025, 4, 30),
            self.crawler.id
        )

        # check that process_water_body.delay is called 3671 times
        self.assertEqual(mock_process_water_body.call_count, 3671)
        self.assertEqual(AnalysisTask.objects.all().count(), 3671)
        crawl_progress = CrawlProgress.objects.first()
        self.assertEqual(crawl_progress.data_to_process, 3671)
        self.assertEqual(crawl_progress.status, Status.RUNNING)
        
        # Rerun same crawler
        process_crawler(
            datetime.date(2025, 4, 1),
            datetime.date(2025, 4, 30),
            self.crawler.id
        )
        
        # check that process_water_body.delay is called 3671 times
        # meaning, the it did not create new AnalysisTask 
        # and call process_water_body
        self.assertEqual(AnalysisTask.objects.all().count(), 3671)
        self.assertEqual(mock_process_water_body.call_count, 3671)
        crawl_progress = CrawlProgress.objects.first()
        self.assertEqual(crawl_progress.data_to_process, 0)

    @patch("project.utils.calculations.analysis.Client")
    @patch("project.utils.calculations.analysis.stac_load")
    def test_run_update_data(self, mock_stac_load, mock_client):
        """
        Test that the update data creates expected output files (AWEI, NDCI, NDTI).
        """

        crawler_progresses = CrawlProgress.objects.all()
        self.assertEqual(crawler_progresses.count(), 0)

        gdf_water_body = self.get_water_body_gdf(box(*self.crawler.bbox.extent))
        gdf_water_body = gdf_water_body[gdf_water_body["uid"] == "k6j618e21q"]

        # Mock stac_load to return dummy xarray.Dataset with necessary bands
        tz_now = timezone.now().replace(year=2025, month=4, day=2)
        with patch("project.tasks.store_data.timezone.now") as mock_tz_now:
            with patch("project.tasks.store_data.gpd.read_file") as mock_read_file:
                mock_read_file.side_effect = [gdf_water_body]
                mock_tz_now.return_value = tz_now
                self.setup_data(mock_stac_load, mock_client)
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

        crawler_progresses = CrawlProgress.objects.all()
        crawler_progress = crawler_progresses.first()
        self.assertEqual(crawler_progress.progress, 100)
        self.assertIsNotNone(crawler_progress.completed_at)
        self.assertEqual(crawler_progress.status, 'completed')

        # check merged file exist
        for indicator_type in ['AWEI', 'NDCI', 'NDTI']:
            self.assertTrue(
                os.path.exists(
                    os.path.join(
                        settings.MEDIA_ROOT,
                        'mosaics',
                        indicator_type,
                        '2025',
                        '03',
                        f'SA_{indicator_type}_2025-03.tif'
                    )
                )
            )
