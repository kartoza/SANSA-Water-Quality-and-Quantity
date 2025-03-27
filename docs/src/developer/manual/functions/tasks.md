# Task Documentation

This section describes the Celery tasks used in the SANSA Water Quantity and Quality Monitoring Platform. Tasks enable long-running or resource-intensive operations to run asynchronously in the background.

---

## `run_analysis`

Launches a complete multi-index water analysis process.

### Description
Triggers analysis based on user-specified parameters such as start/end date, bounding box, resolution, and indicator types (e.g., AWEI, NDCI).

### Parameters
- `start_date`, `end_date`: ISO date strings
- `bbox`: List of bounding box coordinates
- `resolution`: Output resolution in meters (default: 20)
- `export_plot`, `export_nc`, `export_cog`: Toggles for optional outputs
- `calc_types`: List of monitoring indices to calculate
- `task_id`: UUID of the corresponding `AnalysisTask`

---

## `update_stored_data`

Placeholder task for updating stored data.
- Currently logs that the update operation was triggered.
- To be implemented with a data crawling routine in the future.

---

## `compute_water_extent_task`

Calculates the surface area (in km²) of water bodies from a previously generated AWEI raster.

### Description
- Loads the latest AWEI output from a given task
- Applies a threshold and computes area using raster utils
- Adds area log to the task and updates task status

### Parameters
- `task_id`: UUID of the associated task
- `bbox`, `spatial_resolution`, `input_type`, `start_date`, `end_date`: Task metadata
- `threshold`: AWEI threshold to distinguish water vs non-water

### Returns
```json
{
  "area_km2": 73.21,
  "task_id": "...",
  "threshold": 0.0
}
```

---

## `generate_water_mask_task`

Creates a binary water mask raster from a task's AWEI output.

### Description
- Loads the AWEI GeoTIFF file
- Applies a threshold to generate binary mask
- Saves the mask as a new `TaskOutput` file
- Logs completion to `AnalysisTask`

### Parameters
Same as `compute_water_extent_task`

### Returns
```json
{
  "mask_url": "https://.../mask.tif",
  "task_id": "...",
  ...
}
```

---

## Notes

- All tasks use `self.update_state()` to report progress.
- Exceptions are caught and logged to `TaskLog`.
- Each task references `AnalysisTask` for tracking.

These tasks are launched using `.delay(...)` from views or admin panels and are critical to automated water monitoring pipelines.
