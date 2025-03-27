from django.core.management.base import BaseCommand
from project.utils.calculations.water_extent import (calculate_water_extent_from_tif,
                                                     generate_water_mask_from_tif)
import os
import numpy as np
import rasterio


class Command(BaseCommand):

    def handle(self, *args, **options):
        result = calculate_water_extent_from_tif("../AWEI_2024_01.tif")
        print(f"Area: {result['area_km2']}Km2")

        awei_path = os.path.abspath("../AWEI_2024_01.tif")
        mask_output_path = os.path.abspath("awei_water_mask.tif")
        threshold = 0.0  # Default threshold for AWEI water detection

        generate_water_mask_from_tif(awei_path, mask_output_path, threshold)
        print("Water mask saved to:", mask_output_path)
