# Water Extent API

These endpoints allow users to calculate water surface area (using the AWEI index) and generate binary water masks asynchronously. The system tracks task progress via Celery and provides outputs via `task_uuid`.

---

## `POST /api/water-extent/`

### Description
Triggers asynchronous calculation of water surface area (in km²) using satellite data (e.g., Landsat or Sentinel).

### Request Body
| Field              | Type     | Required | Default   | Description |
|-------------------|----------|----------|-----------|-------------|
| `bbox`            | array    | ✅ Yes   | –         | Bounding box as `[minX, minY, maxX, maxY]` |
| `start_date`      | string   | ✅ Yes   | –         | ISO 8601 date string |
| `end_date`        | string   | ✅ Yes   | –         | ISO 8601 date string |
| `spatial_resolution` | int   | ❌ No    | `30`      | Resolution in meters |
| `input_type`      | string   | ❌ No    | `"Landsat"` | Either `"Landsat"` or `"Sentinel"` |

### Response
**HTTP 200 OK**
```json
{
  "message": {
    "task_uuid": "c0a80124-19e4-11ee-be56-0242ac120002"
  }
}
```

---

## `GET /api/water-extent/status/<task_uuid>/`

### Description
Checks the current status of the water extent calculation task and returns the result (if complete).

### Response
**HTTP 200 OK**
```json
{
    "uuid": "c0a80124-19e4-11ee-be56-0242ac120002",
    "task_name": "Water Extent - admin",
    "status": "SUCCESS",
    "parameters": {
        ...
    },
    "started_at": "2025-03-25T11:57:08.611605Z",
    "completed_at": "2025-03-25T11:57:08.694063Z",
    "created_at": "2025-03-25T11:57:08.476018Z",
    "task_outputs": [],
    "area_km2": 47.07
}
```

---

## `POST /api/water-mask/`

### Description
Triggers asynchronous generation of a water mask using the AWEI index.

### Request Body
| Field              | Type     | Required | Default   | Description |
|-------------------|----------|----------|-----------|-------------|
| `bbox`            | array    | ✅ Yes   | –         | Bounding box as `[minX, minY, maxX, maxY]` |
| `spatial_resolution` | int   | ❌ No    | `10`      | Resolution in meters |
| `input_type`      | string   | ❌ No    | `"Sentinel"` | Either `"Landsat"` or `"Sentinel"` |

### Response
**HTTP 200 OK**
```json
{
  "message": {
    "task_uuid": "b4cccd20-3452-11ee-b8c2-0242ac120002"
  }
}
```

---

## `GET /api/water-mask/status/<task_uuid>/`

### Description
Checks the current status of the water mask generation task and returns output metadata.

### Response
**HTTP 200 OK**
```json
{
    "uuid": "b4cccd20-3452-11ee-b8c2-0242ac120002",
    "task_name": "Water Mask - admin",
    "status": "SUCCESS",
    "parameters": {
        ...
    },
    "started_at": "2025-03-25T23:50:27.572167Z",
    "completed_at": "2025-03-25T23:50:27.709532Z",
    "created_at": "2025-03-25T23:50:27.417118Z",
    "task_outputs": [
        {
            "id": 11,
            "file": "http://127.0.0.1:8000/media/2/b4cccd20-3452-11ee-b8c2-0242ac120002/AWEI_2024_01_gbbsZQ1_mask.tif",
            "size": 24918,
            "monitoring_type": "AWEI_MASK",
            "created_at": "2025-03-25T23:50:27.701142Z"
        }
    ]
}
```

---

## Notes

- If a task with identical parameters already exists, it will not be duplicated.
- Use `task_uuid` to track results and download files after processing is complete.
