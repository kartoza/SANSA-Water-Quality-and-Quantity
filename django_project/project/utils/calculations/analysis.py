import logging
import uuid
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from celery.utils.log import get_task_logger
from pystac_client import Client
from odc.stac import configure_rio, stac_load
from project.models import MonitoringIndicatorType

logger = get_task_logger(__name__)


class Analysis:
    """
    Do calculations on the STAC data.
    """
    def __init__(self, start_date, end_date, bbox, 
                 resolution=20, export_plot=True, export_nc=True, 
                 export_cog=True, calc_types=None, task=None
                 ):
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
        self.output = {}

        configure_rio(
            cloud_defaults=True
        )

        # Open the stac catalogue
        catalog = Client.open("https://earth-search.aws.element84.com/v1")

        # Set the STAC collections
        collections = ["sentinel-2-c1-l2a"]

        # Build a query with the set parameters
        query = catalog.search(
            bbox=bbox, 
            collections=collections, 
            datetime=f"{start_date}/{end_date}",
            query={"eo:cloud_cover": {"lt": 20}}  # Optional cloud cover filter
        )
        # Search the STAC catalog for all items matching the query
        self.items = list(query.items())
        self.add_log(f"Found: {len(self.items):d} datasets")

    def add_log(self, log, level=logging.INFO):
        logger.log(level, log)
        if self.task:
            self.task.add_log(log, level=level)

    def run_export_cog(self, month_data, cog_path):
        """Export to Cloud Optimized GeoTIFF.
        """
        import rioxarray
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
        month_data.to_netcdf(
            nc_path,
            engine="netcdf4"
        )

    def run_export_plot(self, month_data, png_path, year, month, calc_type):
        """Export to PNG format.
        """
        self.add_log(f"Saving Plot: {png_path}")
        data_min = float(month_data.min().compute())
        data_max = float(month_data.max().compute())
        if data_min == data_max:
            data_min -= 0.1
            data_max += 0.1

        ax = month_data.plot(
            cmap="BrBG",
            vmin=data_min,
            vmax=data_max
        )
        plt.gca().set_title(f"{calc_type} - {year}-{month:02d}")

        plt.savefig(png_path, dpi=300, bbox_inches='tight')
        plt.close()

    def save_output(self):
        if self.task:
            for calc_type, paths in self.output.items():
                for path in paths:
                    self.add_log(f"Saving output: {path}")
                    self.task.task_outputs.create(
                        file=path,
                        monitoring_type=MonitoringIndicatorType.objects.get(
                            monitoring_indicator_type=calc_type
                        ),
                        size=os.path.getsize(path),
                        created_by=self.task.created_by
                    )

    def run(self):
        """Run the calculations.
        """
        self.add_log("Loading STAC items")

        ds = stac_load(
            self.items,
            bands=("blue", "red", "green", "nir", "swir16", "swir22"),
            crs=self.crs,
            resolution=self.resolution,
            chunks={},
            groupby="solar_day",
            bbox=self.bbox,
        )

        self.add_log("Scale & Resample with coords preserved")
        # Step 1: Scale & Resample with coords preserved
        scaled_ds = ds[["blue", "red", "green", "nir", "swir16", "swir22"]] / 10000.0

        self.add_log("Resample monthly")
        # Step 2: Resample monthly
        monthly_ds = scaled_ds.resample(time="1M").mean()

        # Step 4: Calculate measurement
        for calc_type in self.calc_types:
            self.add_log(f"calculate {calc_type}")
            self.output[calc_type] = []

            if calc_type == "AWEI":
                monthly_ds[calc_type] = 1.0 * monthly_ds.blue + 2.5 * monthly_ds.green - 1.5 * (monthly_ds.nir + monthly_ds.swir16) - 0.25 * monthly_ds.swir22
            elif calc_type == "NDCI":
                monthly_ds[calc_type] = (monthly_ds.red - monthly_ds.blue) / (monthly_ds.red + monthly_ds.blue)
            elif calc_type == "NDTI":
                monthly_ds[calc_type] = (monthly_ds.green - monthly_ds.red) / (monthly_ds.green + monthly_ds.red)
            elif calc_type == "SABI":
                monthly_ds[calc_type] = (monthly_ds.nir - monthly_ds.red) / (monthly_ds.blue + monthly_ds.green)
            elif calc_type == "CDOM":
                monthly_ds[calc_type] = (1 / monthly_ds.blue) - (1 / monthly_ds.green)

            for time_val in monthly_ds.time.values:
                month_data = monthly_ds.get(calc_type).sel(time=time_val)

                dt = pd.to_datetime(str(time_val))
                year = dt.year
                month = dt.month

                cog_path = os.path.join(self.output_dir, f"{calc_type}_{year}_{month:02d}.tif")
                nc_path = os.path.join(self.output_dir, f"{calc_type}_{year}_{month:02d}.nc")
                png_path = os.path.join(self.output_dir, f"{calc_type}_{year}_{month:02d}.png")

                if self.export_plot:
                    self.run_export_plot(month_data, png_path, year, month, calc_type)
                    self.output[calc_type].append(png_path)
                
                if self.export_nc:
                    self.run_export_nc(month_data, nc_path)
                    self.output[calc_type].append(nc_path)

                if self.export_cog:
                    self.run_export_cog(month_data, cog_path)
                    self.output[calc_type].append(cog_path)

        self.save_output()