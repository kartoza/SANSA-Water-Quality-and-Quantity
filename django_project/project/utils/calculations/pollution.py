import os
import json
import logging
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import mapping


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PollutionAnalyzer:

    def __init__(self, ndti_raster, ndci_raster, point_sources, non_point_areas, output_dir):
        """
        Initializes the Pollution Analyzer.

        :param ndti_raster: Path to the computed NDTI raster.
        :param ndci_raster: Path to the computed NDCI raster.
        :param point_sources: Path to point source pollution shapefile.
        :param non_point_areas: Path to non-point source pollution shapefile.
        :param output_dir: Directory to save reports.
        """
        self.ndti_raster = ndti_raster
        self.ndci_raster = ndci_raster
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.point_sources = gpd.read_file(point_sources)
        self.non_point_areas = gpd.read_file(non_point_areas)

    def analyze_pollution(self, raster_path, sources, output_json):
        """
        Computes mean pollution index for given sources (point or non-point).

        :param raster_path: Path to the raster file (NDTI/NDCI).
        :param sources: Geopandas DataFrame containing pollution sources.
        :param output_json: Path to save the JSON report.
        """
        with rasterio.open(raster_path) as src:
            # Reproject raster to EPSG:4326
            dst_crs = 'EPSG:4326'
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds)

            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            # Create in-memory reprojection target
            with rasterio.MemoryFile() as memfile:
                with memfile.open(**kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.nearest
                        )

                    # Now dst is the reprojected raster in EPSG:4326
                    results = []
                    for _, source in sources.iterrows():
                        geom = [mapping(source.geometry)]
                        try:
                            out_image, _ = mask(dst, geom, crop=True)
                            mean_pollution = np.mean(out_image[out_image != dst.nodata])
                            results.append({
                                "id": source["id"],
                                "mean_index": float(mean_pollution) if mean_pollution is not None else None
                            })
                        except Exception as e:
                            logging.warning(f"Skipping {source['id']}: {str(e)}")

        with open(output_json, "w") as f:
            json.dump(results, f, indent=4)

        logging.info(f"Pollution report saved: {output_json}")
        return results

    def generate_reports(self):
        """
        Generates JSON reports for point and non-point source pollution.
        """
        point_report = os.path.join(self.output_dir, "point_source_pollution.json")
        non_point_report = os.path.join(self.output_dir, "non_point_source_pollution.json")

        # Analyze point sources (factories, wastewater plants)
        self.analyze_pollution(self.ndti_raster, self.point_sources, point_report)

        # Analyze non-point sources (agriculture, runoff)
        self.analyze_pollution(self.ndci_raster, self.non_point_areas, non_point_report)

        logging.info("All pollution reports generated.")
