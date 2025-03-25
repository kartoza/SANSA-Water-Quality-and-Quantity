# Water Analysis API

These endpoints allow users to trigger water quality and quantity analysis over a specified time range and geographic region, and to query the status of the analysis task.

---

## `POST /api/water-analysis/`

### Description
Triggers the execution of a water monitoring analysis using satellite imagery (e.g., Sentinel-2, Landsat) over a given time period and bounding box.

The task is executed asynchronously via Celery and results are stored under a unique `task_uuid`.

### Authentication
✅ Token / Basic / Session  
🔒 Requires login (`IsAuthenticated`)

### Request Body (JSON)
| Field           | Type      | Required | Default | Description |
|----------------|-----------|----------|---------|-------------|
| `start_date`    | `string`  | ✅ Yes   | –       | ISO 8601 date (e.g., `"2025-02-01"`) |
| `end_date`      | `string`  | ✅ Yes   | –       | ISO 8601 date (e.g., `"2025-02-28"`) |
| `bbox`          | `array`   | ✅ Yes   | –       | Bounding box as `[minX, minY, maxX, maxY]` |
| `resolution`    | `int`     | ❌ No    | `20`    | Spatial resolution in meters |
| `export_plot`   | `bool`    | ❌ No    | `true`  | Whether to export a PNG plot |
| `export_nc`     | `bool`    | ❌ No    | `true`  | Whether to export NetCDF |
| `export_cog`    | `bool`    | ❌ No    | `true`  | Whether to export Cloud-Optimized GeoTIFFs |
| `calc_types`    | `list`    | ❌ No    | `["AWEI", "NDCI", "NDTI", "SABI", "CDOM"]` | List of indicator types to calculate |

### Example Request
```json
{
  "start_date": "2025-02-01",
  "end_date": "2025-02-28",
  "bbox": [18.3, -34.1, 18.6, -33.9],
  "resolution": 10,
  "export_plot": true,
  "export_nc": false,
  "export_cog": true,
  "calc_types": ["AWEI", "NDCI"]
}
```

### Success Response
**HTTP 200 OK**
```json
{
  "message": {
    "task_uuid": "54c0a878-0be3-4db6-9289-15ff2ae2d239"
  }
}
```

### Error Responses
- **400 Bad Request** – Missing required fields or invalid indicator type
- **500 Internal Server Error** – Task could not be launched

---

## `GET /api/water-analysis/status/<task_uuid>/`

### Description
Checks the status of a previously launched analysis task.

### Parameters
- `task_uuid` (string): The unique identifier for the analysis task (UUID).

### Response
**HTTP 200 OK**
```json
{
  "uuid": "54c0a878-0be3-4db6-9289-15ff2ae2d239",
  "task_name": "Water Analysis demo_user",
  "status": "PENDING",
  "created_at": "2025-03-24T10:30:00Z",
  "result_files": {
    "awei": "https://.../awei_2025-02.tif",
    "ndci": "https://.../ndci_2025-02.nc"
  }
}
```

---

## Calculation Types Reference

| Indicator | Description |
|----------|-------------|
| `AWEI`   | Automated Water Extraction Index – binary water mask |
| `NDCI`   | Normalized Difference Chlorophyll Index – eutrophication marker |
| `NDTI`   | Normalized Difference Turbidity Index – sediment level |
| `SABI`   | Surface Algal Bloom Index – algal activity |
| `CDOM`   | Colored Dissolved Organic Matter |

---

## Notes

- If a task with identical parameters already exists, it will be returned instead of re-executed.
- The task is executed in background using Celery; the client must poll the status endpoint.
- Results will be stored and accessible from `result_files` in the task model once completed.
