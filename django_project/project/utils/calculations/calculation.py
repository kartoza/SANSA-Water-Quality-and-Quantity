from django.core.management.base import BaseCommand
from pystac_client import Client
from django.utils import timezone
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from odc.stac import configure_rio, stac_load


class Calculation:
    def __init__(self, start_date, end_date, bbox, 
                 resolution=20, export_plot=True, export_nc=True, 
                 export_cog=True, values=None
                 ):
        
        if not values:
            values = ["AWEI", "NDTI", "NDCI"]
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
        print(f"Found: {len(self.items):d} datasets")

        self.bbox = bbox
        self.resolution = resolution
        self.crs = "EPSG:6933"
        self.export_plot = export_plot
        self.export_nc = export_nc
        self.export_cog = export_cog

    def run_export_cog(self, month_data, cog_path):
        # === Export to optimized COG ===
        month_data.rio.to_raster(
            cog_path,
            driver="COG",
            compress="DEFLATE",
            predictor=2,
            zlevel=9,
            blocksize=512,
            dtype="float32",
            nodata=np.nan,
            tiled=True,
            overview_resampling="nearest",
            OVERVIEW_LEVELS=[2, 4, 8, 16]  # optional for faster rendering in viewers
        )
        print(f"Saved optimized COG: {cog_path}")

    def run_export_nc(self, month_data, nc_path):
        # === Export to NetCDF ===
        month_data.to_netcdf(
            nc_path,
            engine="netcdf4"
        )
        print(f"Saved NetCDF: {nc_path}")

    def run_export_plot(self, month_data, png_path, year, month):
        # === Export Plot ===
        awei_min = float(month_data.min().compute())
        awei_max = float(month_data.max().compute())
        if awei_min == awei_max:
            awei_min -= 0.1
            awei_max += 0.1

        ax = month_data.plot(
            cmap="BrBG",
            vmin=awei_min,
            vmax=awei_max
        )
        # ax.set_title(f"AWEI - {year}-{month:02d}")
        plt.gca().set_title(f"AWEI - {year}-{month:02d}")

        plt.savefig(png_path, dpi=300, bbox_inches='tight')
        print(f"Saved Plot: {png_path}")

    def run(self):
        print("stac load")
        ds = stac_load(
            self.items,
            bands=("blue", "red", "green", "nir", "swir16", "swir22"),
            crs=self.crs,
            resolution=self.resolution,
            chunks={},
            groupby="solar_day",
            bbox=self.bbox,
        )

        # Step 1: Scale & Resample with coords preserved
        scaled_ds = ds[["blue", "red", "green", "nir", "swir16", "swir22"]] / 10000.0

        # Save coords
        x_coords = ds.x
        y_coords = ds.y

        # Step 2: Resample monthly
        monthly_ds = scaled_ds.resample(time="1M").mean()

        # Step 3: Restore coords
        monthly_ds = monthly_ds.assign_coords({"x": x_coords, "y": y_coords})

        # Step 4: Calculate AWEI
        print("calculate awei")
        monthly_ds['AWEI'] = 1.0 * monthly_ds.blue + 2.5 * monthly_ds.green - 1.5 * (monthly_ds.nir + monthly_ds.swir16) - 0.25 * monthly_ds.swir22


        for time_val in monthly_ds.time.values:
            month_data = monthly_ds.AWEI.sel(time=time_val)
            # # Make sure it is still a 2D DataArray with x and y dims
            # month_data = month_data.squeeze()  # In case there's an extra time dim

            # if "x" not in month_data.dims or "y" not in month_data.dims:
            #     print("Missing spatial dims!")
            #     print(month_data.dims)
            #     continue

            # # Properly assign spatial dimensions and CRS
            # month_data = month_data.rio.set_spatial_dims(x_dim="x", y_dim="y")
            # month_data = month_data.rio.write_crs("EPSG:4326")
            
            dt = pd.to_datetime(str(time_val))
            year = dt.year
            month = dt.month

            cog_path = f"/home/web/project/django_project/AWEI_{year}_{month:02d}.tif"
            nc_path = f"/home/web/project/django_project/AWEI_{year}_{month:02d}.nc"
            png_path = f"/home/web/project/django_project/AWEI_{year}_{month:02d}.png"

            if self.export_plot:
                self.run_export_plot(month_data, png_path, year, month)
            
            if self.export_nc:
                self.run_export_nc(month_data, nc_path)

            if self.export_cog:
                self.run_export_cog(month_data, cog_path)
