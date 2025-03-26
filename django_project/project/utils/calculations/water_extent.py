import rasterio
import numpy as np
import os


def calculate_water_extent_from_tif(tif_path, threshold=0.0):
    with rasterio.open(tif_path) as src:
        awei = src.read(1)
        transform = src.transform
        pixel_area = abs(transform.a * transform.e) / 1e6  # m² → km²

        water_mask = awei > threshold
        water_area_km2 = np.sum(water_mask) * pixel_area

        return {
            "area_km2": round(water_area_km2, 2),
            "width": src.width,
            "height": src.height,
            "crs": str(src.crs),
            "resolution": src.res
        }


def generate_water_mask_from_tif(
        awei_path, mask_output_path=None, threshold=0.0
):
    """
    Generate binary water mask from an AWEI GeoTIFF file.

    Args:
        awei_path (str): Path to the AWEI GeoTIFF file.
        mask_output_path (str): Optional path to save the mask TIFF.
        threshold (float): Threshold above which pixels are considered water.

    Returns:
        dict: Dictionary with mask path and metadata.
    """
    if not os.path.exists(awei_path):
        raise FileNotFoundError(f"AWEI file not found: {awei_path}")

    with rasterio.open(awei_path) as src:
        awei_data = src.read(1)
        profile = src.profile.copy()

        water_mask = (awei_data > threshold).astype(np.uint8)
        profile.update(dtype=rasterio.uint8, count=1, nodata=0)

        if not mask_output_path:
            mask_output_path = os.path.splitext(awei_path)[0] + "_mask.tif"

        with rasterio.open(mask_output_path, "w", **profile) as dst:
            dst.write(water_mask, 1)

    return {
        "mask_path": mask_output_path,
        "threshold": threshold,
        "source": awei_path,
    }
