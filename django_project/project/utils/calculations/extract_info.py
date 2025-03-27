import rasterio
import numpy as np


def extract_tiff_info(image_path):
    """
        Extracts key data from a large TIFF file:
        metadata, statistics, histogram, and no-data pixels.
    """

    with rasterio.open(image_path) as src:
        metadata = {
            "file_name": image_path,
            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,
            "num_bands": src.count,
            "resolution": src.res,
            "driver": src.driver,
            "dtype": src.dtypes[0],
            "nodata_value": src.nodata
        }

        band_stats = {}
        histograms = {}

        for band in range(1, src.count + 1):  # Loop through each band
            stats = {"min": None, "max": None, "mean": None, "std_dev": None, "nodata_pixels": 0}

            histogram = None

            for _, window in src.block_windows(1):  # Read in chunks
                data = src.read(band, window=window).astype(float)

                if src.nodata is not None:
                    nodata_mask = data == src.nodata
                    stats["nodata_pixels"] += np.sum(nodata_mask)
                    data = np.where(nodata_mask, np.nan, data)  # Ignore no-data values in stats

                stats["min"] = np.nanmin(data) if stats["min"] is None else min(
                    stats["min"], np.nanmin(data))
                stats["max"] = np.nanmax(data) if stats["max"] is None else max(
                    stats["max"], np.nanmax(data))
                stats["mean"] = np.nanmean(
                    data) if stats["mean"] is None else (stats["mean"] + np.nanmean(data)) / 2
                stats["std_dev"] = np.nanstd(
                    data) if stats["std_dev"] is None else (stats["std_dev"] + np.nanstd(data)) / 2

                # Compute histogram (10 bins)
                hist, bin_edges = np.histogram(data[~np.isnan(data)], bins=10)
                histogram = hist if histogram is None else histogram + hist

            band_stats[f"Band {band}"] = stats
            histograms[f"Band {band}"] = histogram.tolist()

        return {"metadata": metadata, "band_statistics": band_stats, "histograms": histograms}
