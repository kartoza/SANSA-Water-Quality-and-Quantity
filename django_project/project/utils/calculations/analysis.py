import logging
import uuid
import os
import re
import rioxarray
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from constance import config
from pyproj import CRS
from rasterio.features import shapes
from shapely.geometry import shape
from scipy.ndimage import label, binary_closing
from shapely.geometry import box
from rasterio.warp import transform_bounds

from celery.utils.log import get_task_logger
from pystac_client import Client
from odc.stac import configure_rio, stac_load
from django.core.files import File
from django.utils import timezone
from django.contrib.gis.geos import Polygon
from project.models import MonitoringIndicatorType
from project.models.monitor import TaskOutput
from project.utils.calculations.water_extent import generate_water_mask_from_tif
from collections import defaultdict
from datetime import datetime

logger = get_task_logger(__name__)


class Analysis:
    """
    Do calculations on the STAC data.
    """

    def __init__(self,
                 start_date,
                 end_date,
                 bbox,
                 resolution=20,
                 export_plot=True,
                 export_nc=True,
                 export_cog=True,
                 calc_types=None,
                 task=None,
                 mask_path=None,
                 auto_detect_water=False,
                 image_type='sentinel'):
        self.bbox = bbox
        self.resolution = resolution
        self.crs = "EPSG:6933"
        self.export_plot = export_plot
        self.export_nc = export_nc
        self.export_cog = export_cog
        self.calc_types = calc_types
        if not calc_types:
            self.calc_types = MonitoringIndicatorType.Type.values

        self.uuid = str(uuid.uuid4())
        self.output_dir = os.path.join("/tmp", self.uuid)
        os.makedirs(self.output_dir, exist_ok=True)

        self.task = task
        self.mask_path = mask_path
        self.auto_detect_water = auto_detect_water
        self.image_type = image_type

        configure_rio(cloud_defaults=True)

        self.mask = None
        if mask_path and os.path.exists(mask_path):
            self.mask = rioxarray.open_rasterio(mask_path).isel(band=0)

        # Open the stac catalogue
        catalog = Client.open("https://earth-search.aws.element84.com/v1")

        # Set the STAC collections
        if self.image_type == 'sentinel':
            collections = ["sentinel-2-c1-l2a"]
            self.bands = ("blue", "red", "green", "nir", "swir16", "swir22", "scl")
        else:
            collections = ["landsat-c2-l2"]
            self.bands = ("blue", "red", "green", "nir08", "swir16", "swir22")

        # Build a query with the set parameters
        query = catalog.search(
            bbox=bbox,
            collections=collections,
            datetime=f"{start_date}/{end_date}",
            query={"eo:cloud_cover": {
                "lt": 20
            }}  # Optional cloud cover filter
        )
        # Search the STAC catalog for all items matching the query
        # self.items = list(self.group_tiles_latest_date_catalog(query))
        self.items = list(query.items())
        self.add_log(f"Found: {len(self.items):d} datasets")

    def group_tiles_latest_date_catalog(self, query):
        items = list(query.items())

        # Group items by tile (e.g., assume "mgrs:tile" is in item.properties)
        tiles = defaultdict(list)

        for item in items:
            tile_id = item.properties.get("mgrs:tile") or item.id.split("_")[2]  # adjust this line depending on how tile ID is stored
            tiles[tile_id].append(item)

        # Select the most recent item for each tile
        latest_per_tile = {}

        for tile_id, tile_items in tiles.items():
            latest_item = max(tile_items, key=lambda x: x.datetime)
            latest_per_tile[tile_id] = latest_item

        # Now `latest_per_tile.values()` gives you the latest tile for each tile ID
        print(f"Selected {len(latest_per_tile)} latest tiles")
        return latest_per_tile.values()

    def add_log(self, log, level=logging.INFO):
        print(log)
        logger.log(level, log)
        if self.task:
            self.task.add_log(log, level=level)

    def run_export_cog(self, month_data, cog_path):
        """Export to Cloud Optimized GeoTIFF.
        """
        self.add_log(f"Saving COG: {cog_path}")
        month_data.rio.to_raster(
            cog_path,
            driver="COG",
            compress="DEFLATE",
            predictor=2,
            blocksize=512,
            dtype="float32",
            nodata=np.nan,
            overview_resampling="nearest",
        )

    def run_export_nc(self, month_data, nc_path):
        """Export to NetCDF.
        """
        self.add_log(f"Saving NetCDF: {nc_path}")
        month_data.to_netcdf(nc_path, engine="netcdf4")

    def run_export_plot(self, month_data, png_path, year, month, calc_type):
        """Export to PNG format.
        """
        self.add_log(f"Saving Plot: {png_path}")
        data_min = float(month_data.min().compute())
        data_max = float(month_data.max().compute())
        if data_min == data_max:
            data_min -= 0.1
            data_max += 0.1

        ax = month_data.plot(cmap="BrBG", vmin=data_min, vmax=data_max)  # noqa
        plt.gca().set_title(f"{calc_type} - {year}-{month:02d}")

        plt.savefig(png_path, dpi=300, bbox_inches='tight')
        plt.close()

    def save_output(self, path, calc_type, bbox):
        # Convert bbox list to Polygon if needed
        if isinstance(bbox, list):
            minx, miny, maxx, maxy = bbox
            bbox = Polygon.from_bbox((minx, miny, maxx, maxy))

        match = re.search(r"(\d{4})_(\d{2})" , os.path.basename(path))  # Extract YYYY and MM
        if match:
            year, month = match.groups()
            observation_date = timezone.datetime(
                int(year),
                int(month),
                1,
                tzinfo=timezone.get_current_timezone()
            )

            with open(path, 'rb') as f:
                django_file = File(f)
                output = TaskOutput.objects.create(
                    monitoring_type=MonitoringIndicatorType.objects.get(
                        monitoring_indicator_type=calc_type),
                    task=self.task,
                    size=os.path.getsize(path),
                    created_by=self.task.created_by,
                    bbox=bbox,
                    observation_date=observation_date)
                output.file.save(os.path.basename(path), django_file)
                os.remove(path)
                self.add_log("Output saved")
                return output.file.path

    def apply_mask(self, data_array):
        """Applies the raster mask if available, ensuring proper CRS."""
        if self.mask is not None:
            self.add_log("Applying mask to data")

            # Ensure mask has a CRS
            if self.mask.rio.crs is None:
                raise ValueError(
                    "Mask raster has no CRS. Please provide a valid georeferenced mask.")

            # Reproject mask if needed
            if self.mask.rio.crs != data_array.rio.crs:
                self.add_log(f"Reprojecting mask from {self.mask.rio.crs} to {data_array.rio.crs}")
                self.mask = self.mask.rio.reproject(data_array.rio.crs)

            # Convert raster mask to vector polygons
            self.add_log("Converting raster mask to polygons")
            mask_array = self.mask.values
            mask_transform = self.mask.rio.transform()

            # Extract valid polygons and convert to Shapely objects
            polygons = [
                shape(geom) for geom, value in shapes(mask_array, transform=mask_transform)
                if value > 0
            ]

            if not polygons:
                raise ValueError("No valid mask polygons found.")

            # Create GeoDataFrame correctly

            # Get CRS from data_array and assign it to mask_gdf
            data_array.rio.write_crs(6933, inplace=True)
            correct_crs = CRS.from_epsg(6933)
            mask_gdf = gpd.GeoDataFrame(geometry=polygons, crs=self.mask.rio.crs)
            mask_gdf = mask_gdf.to_crs(correct_crs)

            # Clip data using Shapely geometries
            data_array = data_array.rio.clip(mask_gdf.geometry, all_touched=True, drop=True)

        return data_array

    def extract_water_bodies(self, awei_data, year, month):
        """Extracts and saves multiple large water bodies from AWEI."""
        self.add_log(f"Extracting water bodies for {year}-{month:02d}")
        # Step 1: Apply Water Threshold (AWEI ≥ 0)
        water_mask = (awei_data >= config.AWEI_THRESHOLD).astype(np.uint8)

        # Step 2: Merge Nearby Pixels to Prevent Fragmentation
        water_mask = binary_closing(water_mask, structure=np.ones((3, 3))).astype(np.uint8)

        # Step 3: Label Connected Water Regions (Ensuring Diagonal Connectivity)
        labeled_array, num_features = label(water_mask, structure=np.ones((3, 3)))

        if num_features == 0:
            self.add_log(f"No water bodies found for {year}-{month:02d}")
            return

        self.add_log(f"Found {num_features} water bodies in {year}-{month:02d}")

        # Step 4: Filter Out Small Water Bodies (Noise Removal)
        # Adjust based on resolution (e.g., 100 pixels ≈ 0.2 km²)
        min_pixels = config.WATER_BODY_MIN_PIXEL
        unique_labels, counts = np.unique(labeled_array, return_counts=True)
        large_water_bodies = {
            label
            for label, count in zip(unique_labels, counts) if count >= min_pixels
        }

        # Step 5: Loop Over Each Large Water Body & Save Separately
        for i in large_water_bodies:
            if i == 0:  # Ignore background
                continue

            print(f"Processing water body {i}/{num_features}")

            # Extract the current water body
            water_body = (labeled_array == i).astype(np.uint8)
            masked_awei = awei_data.where(water_body == 1, np.nan)
            nonzero_coords = np.argwhere(water_body)
            if nonzero_coords.size > 0:
                min_y, min_x = nonzero_coords.min(axis=0)
                max_y, max_x = nonzero_coords.max(axis=0)

                # Crop AWEI data to this bounding box
                cropped_awei = masked_awei.isel(y=slice(min_y, max_y + 1),
                                                x=slice(min_x, max_x + 1))
                # Fix: Reassign Coordinates to Match Cropped Data
                cropped_awei = cropped_awei.assign_coords({
                    "y": masked_awei.y[min_y:max_y + 1],
                    "x": masked_awei.x[min_x:max_x + 1]
                })

                # Save as GeoTIFF
                tiff_path = f"{self.output_dir}/{i}_AWEI_{year}_{month:02d}.tif"
                cropped_awei.rio.to_raster(
                    tiff_path,
                    driver="COG",
                    compress="DEFLATE",
                    predictor=2,
                    blocksize=512,
                    dtype="float32",
                    nodata=np.nan,
                    overview_resampling="nearest",
                )

                self.save_output(tiff_path, 'AWEI', self.get_bbox(cropped_awei))
                self.add_log(f"Saved water body {i}/{num_features} for {year}-{month:02d}")

        self.add_log(f"Finished extracting water bodies for {year}-{month:02d}")

    def get_bbox(self, data_array):
        """Extracts bbox from monthly_ds and reprojects it to EPSG:4326."""
        # Get dataset CRS
        dataset_crs = data_array.rio.crs

        if dataset_crs is None:
            raise ValueError("monthly_ds does not have a valid CRS")

        # Extract bounding box (minx, miny, maxx, maxy)
        minx, miny, maxx, maxy = data_array.rio.bounds()

        # Transform bbox to EPSG:4326 if necessary
        if dataset_crs.to_epsg() != 4326:
            minx, miny, maxx, maxy = transform_bounds(
                dataset_crs, "EPSG:4326", minx, miny, maxx, maxy
            )

        # Convert to Django PolygonField format
        bbox_polygon = [minx, miny, maxx, maxy]

        return bbox_polygon

    def run(self):
        """Run the calculations.
        """
        self.add_log("Loading STAC items")

        ds = stac_load(
            self.items,
            bands=self.bands,
            crs=self.crs,
            resolution=self.resolution,
            chunks={},
            groupby="solar_day",
            bbox=self.bbox,
            band_aliases={"nir": "nir08"}
        )

        if self.image_type == 'landsat':
            ds = ds.rename({"nir08": "nir"})

        self.add_log("Scale & Resample with coords preserved")
        # Step 1: Scale & Resample with coords preserved
        scaled_ds = ds[["blue", "red", "green", "nir", "swir16", "swir22"]] / 10000.0

        self.add_log("Resample monthly")
        # Step 2: Resample monthly
        if self.image_type == 'sentinel':
            cloud_mask = (ds.scl != 9) & (ds.scl != 10)
            monthly_ds = scaled_ds.where(cloud_mask).resample(time="1M").mean()
        else:
            monthly_ds = scaled_ds.resample(time="1M").mean()

        # Step 4: Calculate measurement
        for calc_type in self.calc_types:
            self.add_log(f"calculate {calc_type}")

            if calc_type == "AWEI":
                monthly_ds[calc_type] = 1.0 * monthly_ds.blue + 2.5 * monthly_ds.green - 1.5 * (
                    monthly_ds.nir + monthly_ds.swir16) - 0.25 * monthly_ds.swir22
            elif calc_type == "NDCI":
                monthly_ds[calc_type] = (monthly_ds.red - monthly_ds.blue) / (monthly_ds.red +
                                                                              monthly_ds.blue)
            elif calc_type == "NDTI":
                monthly_ds[calc_type] = (monthly_ds.green - monthly_ds.red) / (monthly_ds.green +
                                                                               monthly_ds.red)
            elif calc_type == "SABI":
                monthly_ds[calc_type] = (monthly_ds.nir - monthly_ds.red) / (monthly_ds.blue +
                                                                             monthly_ds.green)
            elif calc_type == "CDOM":
                monthly_ds[calc_type] = (1 / monthly_ds.blue) - (1 / monthly_ds.green)

            monthly_ds = monthly_ds.sortby("y")
            monthly_ds[calc_type] = monthly_ds[calc_type].interpolate_na(
                dim="x", method="nearest").interpolate_na(dim="y", method="nearest")

            for time_val in monthly_ds.time.values:
                month_data = monthly_ds.get(calc_type).sel(time=time_val)
                month_data = self.apply_mask(month_data)

                dt = pd.to_datetime(str(time_val))
                year = dt.year
                month = dt.month

                cog_path = os.path.join(self.output_dir, f"{calc_type}_{year}_{month:02d}.tif")
                nc_path = os.path.join(self.output_dir, f"{calc_type}_{year}_{month:02d}.nc")
                png_path = os.path.join(self.output_dir, f"{calc_type}_{year}_{month:02d}.png")

                if self.export_plot:
                    self.run_export_plot(month_data, png_path, year, month, calc_type)
                    self.save_output(png_path, calc_type, self.get_bbox(month_data))

                if self.export_nc:
                    self.run_export_nc(month_data, nc_path)
                    self.save_output(nc_path, calc_type, self.get_bbox(month_data))

                if self.export_cog:
                    if calc_type == "AWEI":
                        if self.auto_detect_water:
                            self.extract_water_bodies(month_data, year, month)
                        else:
                            self.run_export_cog(month_data, cog_path)
                            cog_path = generate_water_mask_from_tif(
                                cog_path,
                                threshold=config.AWEI_TRESHOLD
                            )['mask_path']
                            self.save_output(cog_path, calc_type, self.get_bbox(month_data))
                    else:
                        self.run_export_cog(month_data, cog_path)
                        self.save_output(cog_path, calc_type, self.get_bbox(month_data))
