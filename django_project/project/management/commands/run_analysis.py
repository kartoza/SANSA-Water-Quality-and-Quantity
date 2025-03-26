from django.core.management.base import BaseCommand
from pystac_client import Client
from django.utils import timezone
import pandas as pd

import matplotlib.pyplot as plt
from odc.stac import configure_rio, stac_load
from project.utils.calculations.analysis import Analysis
from project.models import AnalysisTask


class Command(BaseCommand):
    help = 'This is a custom command that prints a simple message.'

    def handle(self, *args, **options):
        start = timezone.now()
        task = AnalysisTask.objects.get(uuid='e6d83fad-c5c4-46e8-9fa3-2d5daedc07b5')

        parameters = {
            "bbox": [19.071814670776433, -34.10465768253897, 19.32407544986191, -33.954845668837194], 
            "end_date": "2025-01-31", 
            "export_nc": False, 
            "calc_types": ["NDTI", "NDCI"], 
            "export_cog": True, 
            "resolution": 20, 
            "start_date": "2025-01-01", 
            "export_plot": False,
            "task": task,
            "mask_path": "/home/web/media/2/e6d83fad-c5c4-46e8-9fa3-2d5daedc07b5/AWEI_2025_01_mask.tif"
        }
        
        calculation = Analysis(**parameters)
        calculation.run()

        end = timezone.now()
        runtime = end - start
        runtime.total_seconds()

        print(f"Total runtime: {runtime.total_seconds():.2f} seconds")

