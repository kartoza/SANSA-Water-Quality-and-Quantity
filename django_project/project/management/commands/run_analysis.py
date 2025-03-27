from django.core.management.base import BaseCommand
from pystac_client import Client
from django.utils import timezone
import pandas as pd

import matplotlib.pyplot as plt
from odc.stac import configure_rio, stac_load
from project.utils.calculations.analysis import Analysis
from project.models import AnalysisTask


class Command(BaseCommand):
    help = 'This is a custom command to manually call Analysis.'

    def handle(self, *args, **options):
        start = timezone.now()
        task = AnalysisTask.objects.get(uuid='e6d83fad-c5c4-46e8-9fa3-2d5daedc07b5')
        bbox = [18.9642798271509356, -34.1575977741685364, 19.3228608906262345, -33.8841992864707748]
        bbox_small = [19.071814670776433, -34.10465768253897, 19.32407544986191, -33.954845668837194]
        bbox_smallest = [19.05369441613876, -33.846438941213165, 19.122644628304158, -33.793868168094917]
        bbox_biggest = [18.5730906651792189, -34.3719396597160198, 20.1357171906862611, -33.5365612416096894]
        berg_river_dam_bbox = [19.0268418935902162, -33.9569226968783084, 19.1338788226037124, -33.8997008726108362]

        parameters = {
            "bbox": berg_river_dam_bbox, 
            "end_date": "2025-01-31", 
            "export_nc": False, 
            "calc_types": ["AWEI"], 
            "export_cog": True, 
            "resolution": 20, 
            "start_date": "2025-01-01", 
            "export_plot": False,
            "task": task,
            # "mask_path": "/home/web/media/2/e6d83fad-c5c4-46e8-9fa3-2d5daedc07b5/AWEI_2025_01_mask.tif",
            "auto_detect_water": True
        }
        
        calculation = Analysis(**parameters)
        calculation.run()

        end = timezone.now()
        runtime = end - start
        runtime.total_seconds()

        print(f"Total runtime: {runtime.total_seconds():.2f} seconds")