import os
import subprocess
import tempfile


def create_mosaic(vrt_path: str, raster_paths: list, output_path: str):
    raster_paths = [
        rpath for rpath in raster_paths if os.path.exists(rpath)
    ]
    if not raster_paths:
        print("No valid raster files found.")
        return

    print(f"Found {len(raster_paths)} raster(s).")

    # Step 2: Create VRT
    with tempfile.NamedTemporaryFile(suffix=".vrt", delete=False) as vrt_file:
        vrt_path = vrt_file.name

    print("Creating VRT...")
    subprocess.run(
        ["gdalbuildvrt", vrt_path] + raster_paths,
        check=True
    )

    # Step 3: Translate VRT to COG
    print("Converting VRT to COG...")
    subprocess.run([
        "gdal_translate",
        "-of", "COG",
        "-co", "COMPRESS=LZW",
        "-co", "TILING_SCHEME=GoogleMapsCompatible",
        vrt_path,
        output_path
    ], check=True)

    os.remove(vrt_path)
