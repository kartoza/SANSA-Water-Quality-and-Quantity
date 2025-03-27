# Utility Functions and Analysis Classes

This section documents the core utility classes and functions powering satellite-based water monitoring and pollution assessment in the SANSA platform. These tools cover everything from data ingestion to raster processing, statistical reporting, and pollution analysis.

---

## `Analysis` Class

Used by Celery tasks to process Sentinel-2 imagery via STAC and compute monthly indicators.

### Key Features:
- Loads imagery from AWS Earth Search (via STAC)
- Computes water-related indices: AWEI, NDCI, NDTI, SABI, CDOM
- Outputs results in multiple formats (COG, NetCDF, PNG)
- Writes logs and uploads files to `TaskOutput`

### Parameters:
- `bbox`: Geographic bounds
- `start_date` / `end_date`: Time window
- `resolution`: Spatial resolution in meters
- `calc_types`: Index types to compute (optional)
- `task`: Reference to `AnalysisTask` for logging/output saving

---

## `CalculateMonitoring` Class

A streamlined version of `Analysis` used for non-Celery batch runs or debugging. It prints outputs directly to console and doesn’t integrate with the Django task model.

Same calculation and export logic as `Analysis`, but decoupled from the Django task system.

---

## `calculate_indices(image_path, bands, output_dir)`

A raster-based implementation that computes four remote sensing indices from raw Sentinel-2 bands.

### Output Indices:
- **AWEI_sh**: For shadow removal
- **AWEI_ns**: For general water detection
- **NDTI**: Turbidity proxy
- **NDCI**: Chlorophyll-related metric

### Notes:
- Reads/writes block-by-block using `window` iteration
- Optimized for large TIFFs

---

## `calculate_water_extent_from_tif(tif_path, threshold=0.0)`

Calculates surface water area from AWEI raster output. Uses a pixel-wise threshold and multiplies by pixel area to get total km².

### Returns:
- Surface area
- Geo-metadata (CRS, width, height)

Used in: `compute_water_extent_task`

---

## `generate_water_mask_from_tif(...)`

Generates a binary water mask from an AWEI GeoTIFF by applying a threshold. Optimized to handle large raster files using chunked windows.

### Output:
- New mask TIFF file path
- Metadata: resolution, CRS, threshold used

Used in: `generate_water_mask_task`

---

## `extract_tiff_info(image_path)`

Extracts metadata and statistics from multi-band TIFFs:
- Band-wise min, max, mean, std_dev
- Histogram counts
- No-data pixel count
- Raster metadata (size, resolution, CRS)

Outputs are JSON-ready and ideal for audit dashboards.

---

## `PollutionAnalyzer` Class

Used to assess pollution intensity based on raster index values (NDTI and NDCI) over known source locations (factories, farms).

### Inputs:
- Point and polygon shapefiles
- Corresponding index rasters (NDTI/NDCI)

### Outputs:
- JSON reports with mean index per geometry
- Logs for skipped geometries

### Use Case:
- Water pollution attribution
- Hotspot identification
- Risk mapping

---
