# Dataset API

This endpoint provides an overview of all datasets stored in the SANSA Water Monitoring Platform. It supports filtering, pagination, and includes metadata summaries and dataset category counts.

---

## `GET /api/datasets/`

### Description
Retrieves:
- A paginated list of datasets
- Count of datasets by category (`DatasetType`)
- Creation date range (`min_date`, `max_date`)

### Authentication
- Required: Yes (`Token`, `Session`, or `Basic`)
- Permission: `IsAuthenticated`

---

### Query Parameters

| Parameter        | Type   | Required | Description                        |
|------------------|--------|----------|------------------------------------|
| `dataset_type`   | string | No       | Filter datasets by category name  |
| `page`           | int    | No       | Pagination page number            |

---

### Response (Paginated)

```json
{
  "count": 35,
  "next": "/api/datasets/?page=2",
  "previous": null,
  "results": {
    "total_entries": 35,
    "data_categories": [
      {"name": "Satellite", "count": 20},
      {"name": "In-Situ", "count": 15}
    ],
    "metadata": {
      "min_date": "2023-01-05T12:01:00Z",
      "max_date": "2025-03-26T09:47:00Z"
    },
    "datasets": [
      {
        "id": 1,
        "name": "Sentinel NDVI for Limpopo",
        "description": "Vegetation index dataset",
        "dataset_type": {
          "name": "Satellite",
          ...
        },
        "created_at": "...",
        ...
      }
    ]
  }
}
```

---

### Features

- Efficient pagination with default page size: `10`
- Uses `select_related` for optimized DB queries
- Dataset type aggregation using `annotate(Count)`
- Summary stats using `aggregate(Min, Max)`

---
