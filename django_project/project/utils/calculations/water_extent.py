import rasterio
import numpy as np
import os
from rasterio.windows import Window


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


def generate_water_mask_from_tif(awei_path, mask_output_path=None, threshold=0.0, chunk_size=1024):
    """
    Generate binary water mask from an AWEI GeoTIFF file, optimized for large rasters.

    Args:
        awei_path (str): Path to the AWEI GeoTIFF file.
        mask_output_path (str): Optional path to save the mask TIFF.
        threshold (float): Threshold above which pixels are considered water.
        chunk_size (int): Size of the chunks to process (default: 1024x1024).

    Returns:
        dict: Dictionary with mask path and metadata.
    """
    if not os.path.exists(awei_path):
        raise FileNotFoundError(f"AWEI file not found: {awei_path}")

    with rasterio.open(awei_path) as src:
        profile = src.profile.copy()
        profile.update(dtype=rasterio.uint8, count=1, nodata=0)

        if not mask_output_path:
            mask_output_path = os.path.splitext(awei_path)[0] + "_mask.tif"

        with rasterio.open(mask_output_path, "w", **profile) as dst:
            for j in range(0, src.height, chunk_size):
                for i in range(0, src.width, chunk_size):
                    # Define the window size
                    win = Window(i, j, min(chunk_size, src.width - i),
                                 min(chunk_size, src.height - j))

                    # Read the chunk
                    awei_chunk = src.read(1, window=win)

                    # Apply threshold
                    water_mask_chunk = (awei_chunk > threshold).astype(np.uint8)

                    # Write the chunk
                    dst.write(water_mask_chunk, 1, window=win)

    return {
        "mask_path": mask_output_path,
        "threshold": threshold,
        "source": awei_path,
    }
