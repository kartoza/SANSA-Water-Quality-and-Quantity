import rasterio
import numpy as np

# use this bands for Sentinel-2.
bands_sentinel2 = {
    "blue": 2,
    "green": 3,
    "red": 4,
    "nir": 8,
    "swir1": 11,
    "swir2": 12,
    "red_edge": 5
}


def calculate_indices(image_path, bands, output_dir):
    with rasterio.open(image_path) as src:
        profile = src.profile
        profile.update(dtype=rasterio.float32, count=4)  # 4 indices: AWEI_sh, AWEI_ns, NDTI, NDCI

        # Create output file paths
        output_files = {
            "AWEI_sh": f"{output_dir}/AWEI_sh.tif",
            "AWEI_ns": f"{output_dir}/AWEI_ns.tif",
            "NDTI": f"{output_dir}/NDTI.tif",
            "NDCI": f"{output_dir}/NDCI.tif"
        }

        # Open output files for writing
        with rasterio.open(output_files["AWEI_sh"], "w", **profile) as dst_awei_sh, \
             rasterio.open(output_files["AWEI_ns"], "w", **profile) as dst_awei_ns, \
             rasterio.open(output_files["NDTI"], "w", **profile) as dst_ndti, \
             rasterio.open(output_files["NDCI"], "w", **profile) as dst_ndci:

            for ji, window in src.block_windows(1):  # Iterate through windows
                # Read required bands using the window
                blue = src.read(bands['blue'], window=window).astype(float)
                green = src.read(bands['green'], window=window).astype(float)
                red = src.read(bands['red'], window=window).astype(float)
                nir = src.read(bands['nir'], window=window).astype(float)
                swir1 = src.read(bands['swir1'], window=window).astype(float)
                swir2 = src.read(bands['swir2'], window=window).astype(float)
                red_edge = src.read(bands['red_edge'], window=window).astype(float)

                # Compute indices
                awei_sh = (4 * (green - swir1)) - (0.25 * nir) + (2.75 * swir2)
                awei_ns = blue + (2.5 * green) - (1.5 * (nir + swir1)) - (0.25 * swir2)
                ndti = np.divide((red - green), (red + green),
                                 out=np.zeros_like(red),
                                 where=(red + green) != 0)
                ndci = np.divide((red_edge - red), (red_edge + red),
                                 out=np.zeros_like(red),
                                 where=(red_edge + red) != 0)

                # Write output
                dst_awei_sh.write(awei_sh.astype(rasterio.float32), window=window, indexes=1)
                dst_awei_ns.write(awei_ns.astype(rasterio.float32), window=window, indexes=1)
                dst_ndti.write(ndti.astype(rasterio.float32), window=window, indexes=1)
                dst_ndci.write(ndci.astype(rasterio.float32), window=window, indexes=1)

        return output_files
