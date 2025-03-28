## 1 API Endpoints

### 1.1 Get Overview of All Data Crawled

**URL:** `/api/datasets`  
**Content-Type:** `application/json`  
**Method:** `GET`  
**Description:** This endpoint returns all saved data categorized by dataset type and includes filters for querying specific information. Additionally, it provides summary statistics where applicable.

#### Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer <your_token_here>
```

If no token is provided or if the token is invalid, the request will return a `401 Unauthorized` error.

#### Request Parameters

| Parameter | Type    | Required | Description |
|-----------|--------|----------|-------------|
| library   | string | optional | Filter by dataset category (e.g., AWEI, NDTI, NDCI, SABI, Coloured Dissolved Organic Matter). |
| dataset   | string | optional | Filter if dataset is Landsat or Sentinel. |
| format    | string | optional | Filter by output format (e.g., TIFF, Shapefile, RASTER). |
| summary   | boolean | optional | If set to true, returns summary statistics instead of raw data. |
| bbox      | array  | optional | Add a bounding box to filter data for specific areas. |

#### Example Request 

```
GET http://example.com/api/datasets?library=AWEI&dataset=Landsat&format=TIFF&summary=true&bbox=102.0,0.5,103.0,1.5
Authorization: Bearer YOUR_JWT_TOKEN
```


#### Response Structure

**Success Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "category": "AWEI",
      "source": "Landsat/Sentinel",
      "resolution": "10m to 300m",
      "output_format": "TIFF",
      "file_path": "/uploads/image.tiff",
      "date_crawled": "05/02/2025",
      "bbox": [[102.0, 0.5], [102.0, 0.5], [102.0, 0.5], [102.0, 0.5]]
    }
  ],
  "summary": {
    "total_entries": 1,
    "categories": ["AWEI"],
    "unique_sources": ["Landsat", "Sentinel"],
    "resolutions": ["10m", "100m", "300m"],
    "formats": ["TIFF", "RASTER", "Shapefile"]
  }
}
```

**Error Response (400 Bad request)**

```json
{
  "status": "error",
  "message": "Invalid filter parameter"
}
```

**401 Unauthorized** (When no token is provided or the token is invalid)

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token"
}
```

#### Edge Cases & Boundary Conditions
- **Empty Filters:** API should return all available datasets if no filters are applied.
- **Invalid Format:** If an unsupported format is requested, the API should return a `400 Bad Request`.
- **Large Dataset Request:** If the response is too large, API should implement pagination or return an appropriate error.
- **Bounding Box Precision:** Edge cases should verify how precise the bounding box needs to be for filtering.

#### Test Cases
| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Retrieve all datasets | No filters | Returns a list of all datasets |
| Filter by dataset type | `dataset=Landsat` | Returns only Landsat datasets |
| Invalid dataset type | `dataset=InvalidType` | Returns 400 Bad Request |
| Summary statistics | `summary=true` | Returns only summary details |
| Send POST request | `POST /api/saved-datasets` | Returns 405 Method Not Allowed |
| Send PUT request | `PUT /api/saved-datasets` | Returns 405 Method Not Allowed |
| Send DELETE request | `DELETE /api/saved-datasets` | Returns 405 Method Not Allowed |
| Missing Bearer Token | No `Authorization` header | Returns 401 Unauthorized |
| Invalid Bearer Token | `Authorization: Bearer invalid_token` | Returns 401 Unauthorized |

---

### 1.1.1 Get Dataset by ID

**URL:** `/api/datasets/{id}`  
**Content-Type:** `application/json`  
**Method:** `GET`  
**Description:** This endpoint retrieves a specific dataset by its unique ID. The dataset information returned includes metadata, the data file path, and additional details about the dataset.

#### Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer <your_token_here>
```

If no token is provided or if the token is invalid, the request will return a `401 Unauthorized` error.

#### Request Parameters

| Parameter | Type   | Required | Description                      |
|-----------|--------|----------|----------------------------------|
| id        | string | required | The unique identifier for the dataset. |

#### Example Request 

```
GET http://example.com/api/datasets?library=AWEI&dataset=Landsat&format=TIFF&summary=true&bbox=102.0,0.5,103.0,1.5
Authorization: Bearer YOUR_JWT_TOKEN
```


#### Response Structure

**Success Response (200 OK)**

```json
{
  "status": "success",
  "data":
    {
      "id": 1,
      "category": "AWEI",
      "source": "Landsat/Sentinel",
      "resolution": "10m to 300m",
      "output_format": "TIFF",
      "file_path": "/uploads/image.tiff",
      "date_crawled": "05/02/2025",
      "bbox": [[102.0, 0.5], [102.0, 0.5], [102.0, 0.5], [102.0, 0.5]]
    }
}
```

**Error Response (404 Not Found)**

```json
{
  "status": "error",
  "message": "Dataset with the given ID not found"
}
```

**Error Response (400 Bad request)**

```json
{
  "status": "error",
  "message": "Invalid filter parameter"
}
```

**401 Unauthorized** (When no token is provided or the token is invalid)

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token"
}
```

#### Edge Cases & Boundary Conditions
- **Empty Filters:** API should return all available datasets if no filters are applied.
- **Invalid Format:** If an unsupported format is requested, the API should return a `400 Bad Request`.
- **Large Dataset Request:** If the response is too large, API should implement pagination or return an appropriate error.
- **Bounding Box Precision:** Edge cases should verify how precise the bounding box needs to be for filtering.

#### Test Cases
| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Retrieve existing dataset | `id=1` | 	Returns the dataset details for ID 1|
| Dataset not found | `id=999` | Returns 404 Not Found|
| Invalid dataset ID | `id=abc` | Returns 400 Bad Request |
| Send POST request | `POST /api/saved-datasets` | Returns 405 Method Not Allowed |
| Send PUT request | `PUT /api/saved-datasets` | Returns 405 Method Not Allowed |
| Send DELETE request | `DELETE /api/saved-datasets` | Returns 405 Method Not Allowed |
| Missing Bearer Token | No `Authorization` header | Returns 401 Unauthorized |
| Invalid Bearer Token | `Authorization: Bearer invalid_token` | Returns 401 Unauthorized |

---

### 1.2 Automated Water Extraction Index (AWEI)

**URL:** `/api/awei-water-mask`  
**Method:** `GET`  
**Content-Type:** `application/json`  
**Description:** This endpoint provides access to the water mask for extraction of river, lake, and reservoir boundaries as set by the request parameters.

#### Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer <your_token_here>
```

If no token is provided or if the token is invalid, the request will return a `401 Unauthorized` error.

#### Request Parameters

| Parameter          | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| spatial_resolution | int    | optional | Filter by spatial resolution. |
| start_date        | Date (DD/MM/YYYY) | optional | Filter by dataset start date. |
| end_date          | Date (DD/MM/YYYY) | optional | Filter by dataset end date. |
| bbox             | array  | required  | Add a bounding box to filter data for specific areas. |
| input_type        | string | required  | Filter by Landsat/Sentinel. |

#### Response Structure

**Success Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "elevation_data",
      "file_url": "http://example.com/awei/water_mask.tif"
    }
  ]
}
```

**Error Response (400 Bad request)**

```json
{
  "status": "error",
  "message": "Invalid bounding box"
}
```

**401 Unauthorized** (When no token is provided or the token is invalid)

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token"
}
```

#### Edge Cases & Boundary Conditions
- **Missing Bounding Box:** API should return an error if `bbox` is missing.
- **Invalid Date Format:** If dates are not in `DD/MM/YYYY` format, the request should fail.
- **Large Bounding Box:** A large bounding box should return an appropriate number of results without timeout issues.



#### Test Cases
| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Valid request | `bbox=[102.0, 0.5, 103.0, 1.5]` | Returns a water mask |
| Missing bbox | No `bbox` parameter | Returns 400 Bad Request |
| Invalid input type | `input_type=Unknown` | Returns 400 Bad Request |
| Send POST request | `POST /api/awei-water-mask` | Returns 405 Method Not Allowed |
| Send PUT request | `PUT /api/awei-water-mask` | Returns 405 Method Not Allowed |
| Send DELETE request | `DELETE /api/awei-water-mask` | Returns 405 Method Not Allowed |
| Missing Bearer Token | No `Authorization` header | Returns 401 Unauthorized |
| Invalid Bearer Token | `Authorization: Bearer invalid_token` | Returns 401 Unauthorized |

---

### 1.2.1 Water Surface Area Extent Calculation

**URL:** `/api/awei-water-extent`  
**Method:** `GET`  
**Content-Type:** `application/json`  
**Description:** This endpoint calculates the water surface area extent based on the provided parameters.

#### Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer <your_token_here>
```

If no token is provided or if the token is invalid, the request will return a `401 Unauthorized` error.

#### Request Parameters

| Parameter          | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| spatial_resolution | int    | optional | Filter by spatial resolution. |
| start_date        | Date (DD/MM/YYYY) | optional | Filter by dataset start date. |
| end_date          | Date (DD/MM/YYYY) | optional | Filter by dataset end date. |
| bbox             | array  | required  | Add a bounding box to filter data for specific areas. |
| input_type        | string | required  | Filter by dataset type (Landsat/Sentinel). |

#### Response Structure

**Success Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "water_extent_data",
      "file_url": "http://example.com/water_extent.tif"
    }
  ]
}
```

**Error Response (400 Bad Request)**

```json
{
  "status": "error",
  "message": "Invalid bounding box"
}
```

**401 Unauthorized** (When no token is provided or the token is invalid)

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token"
}
```

#### Edge Cases & Boundary Conditions
- **Missing Bounding Box:** API should return an error if `bbox` is missing.
- **Invalid Date Format:** If dates are not in `DD/MM/YYYY` format, the request should fail.
- **Large Bounding Box:** A large bounding box should return an appropriate number of results without timeout issues.

#### Test Cases
| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Valid request | `bbox=[102.0, 0.5, 103.0, 1.5]` | Returns water extent data |
| Missing bbox | No `bbox` parameter | Returns 400 Bad Request |
| Invalid input type | `input_type=Unknown` | Returns 400 Bad Request |
| Send POST request | `POST /api/water-extent` | Returns 405 Method Not Allowed |
| Send PUT request | `PUT /api/water-extent` | Returns 405 Method Not Allowed |
| Send DELETE request | `DELETE /api/water-extent` | Returns 405 Method Not Allowed |
| Missing Bearer Token | No `Authorization` header | Returns 401 Unauthorized |
| Invalid Bearer Token | `Authorization: Bearer invalid_token` | Returns 401 Unauthorized |

---


### 1.3 Normalized Difference Turbidity Index (NDTI)

**URL:** `/api/ndti`  
**Content-Type:** `application/json`  
**Method:** `GET`  
**Description:** This endpoint returns a raster for NDTI as well as necessary data calculated for water pollution, sedimentation in rivers, lakes, and dams.

#### Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer <your_token_here>
```

If no token is provided or if the token is invalid, the request will return a `401 Unauthorized` error.

#### Request Parameters

| Parameter          | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| spatial_resolution | int    | optional | Filter by spatial resolution. |
| start_date        | Date (DD/MM/YYYY) | optional | Filter by dataset start date. |
| end_date          | Date (DD/MM/YYYY) | optional | Filter by dataset end date. |
| bbox             | array  | required  | Add a bounding box to filter data for specific areas. |
| input_type        | string | required  | Filter by Landsat/Sentinel. |

#### Response Structure

**Success Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "elevation_data",
      "file_url": "http://example.com/ndti/mask.tif",
      "possible_point_pollution": {},
      "possible_non-point_pollution": {},
      "water_pollution": {},
      "sediment": {}
    }
  ]
}
```

**Error Response (400 Bad request)**

```json
{
  "status": "error",
  "message": "Invalid bounding box"
}
```

**401 Unauthorized** (When no token is provided or the token is invalid)

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token"
}
```


#### Edge Cases & Boundary Conditions
- **Dataset Availability:** Some datasets may not exist for certain spatial resolutions.
- **Date Range Issues:** If `end_date` is before `start_date`, the request should fail.
- **Precision Loss in Large Bounding Box:** Ensure data is accurately retrieved for large bounding boxes.

#### Test Cases
| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Valid request | `bbox=[100.0, 0.0, 101.0, 1.0]` | Returns NDTI data |
| Invalid date range | `start_date=01/01/2025, end_date=01/01/2024` | Returns 400 Bad Request |
| Unsupported spatial resolution | `spatial_resolution=5000` | Returns 400 Bad Request |
| Send POST request | `POST /api/ndti` | Returns 405 Method Not Allowed |
| Send PUT request | `PUT /api/ndti` | Returns 405 Method Not Allowed |
| Send DELETE request | `DELETE /api/ndti` | Returns 405 Method Not Allowed |
| Missing Bearer Token | No `Authorization` header | Returns 401 Unauthorized |
| Invalid Bearer Token | `Authorization: Bearer invalid_token` | Returns 401 Unauthorized |

---

### 1.4 Normalized Difference Chlorophyll Index (NDCI)

**URL:** `/api/ndci`  
**Content-Type:** `application/json`  
**Method:** `GET`  
**Description:** This endpoint returns a raster for NDCI as well as necessary data calculated for water pollution, sedimentation in rivers, lakes, and dams.

#### Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer <your_token_here>
```

If no token is provided or if the token is invalid, the request will return a `401 Unauthorized` error.

#### Request Parameters

| Parameter          | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| spatial_resolution | int    | optional | Filter by spatial resolution. |
| start_date        | Date (DD/MM/YYYY) | optional | Filter by dataset start date. |
| end_date          | Date (DD/MM/YYYY) | optional | Filter by dataset end date. |
| bbox             | array  | required  | Add a bounding box to filter data for specific areas. |
| input_type        | string | required  | Filter by Landsat/Sentinel. |
| air_temperature   | float  | optional | Add the air temperature for the atmospheric model. |
| relative_humidity | float  | optional | Add the humidity for the atmospheric model. |
| wind_speed        | float  | optional | Add the wind speed for the atmospheric model. |
| precipitation     | float  | optional | Add the precipitation for the atmospheric model. |
| solar_radiation   | float  | optional | Add the solar radiation for the atmospheric model. |

#### Response Structure

**Success Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "elevation_data",
      "file_url": "http://example.com/ndci/mask.tif",
      "possible_point_pollution": {
        "industrial_discharge": "Detected near site X",
        "wastewater_treatment": "Moderate contamination",
      },
      "possible_non-point_pollution": {
        "agricultural_runoff": "High nitrate levels detected",
        "urban_stormwater": "Trace pollution identified",
      },
      "water_pollution": {
        "chlorophyll_a": "Elevated levels detected",
        "turbidity": "Moderate",
      },
      "sediment": {
        "sediment_load": "High during rainy season",
        "source": "Erosion from upstream",
      }
    }
  ]
}
```

**Error Response (400 Bad request)**

```json
{
  "status": "error",
  "message": "Invalid bounding box"
}
```

**401 Unauthorized** (When no token is provided or the token is invalid)

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token"
}
```


#### Edge Cases & Boundary Conditions
- **Extreme Weather Values:** Ensure the system can handle values at the high and low extremes of air temperature, wind speed, etc.
- **Missing Input Type:** `input_type` is required; missing it should return an error.
- **Negative Values:** Parameters like `precipitation` and `solar_radiation` should not accept negative values.

#### Test Cases
| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Valid request with weather params | `bbox=[100.0, 0.0, 101.0, 1.0], air_temperature=30.5` | Returns NDCI data |
| Missing input type | No `input_type` | Returns 400 Bad Request |
| Extreme temperature | `air_temperature=-100` | Returns 400 Bad Request |
| Send POST request | `POST /api/ndti` | Returns 405 Method Not Allowed |
| Send PUT request | `PUT /api/ndti` | Returns 405 Method Not Allowed |
| Send DELETE request | `DELETE /api/ndti` | Returns 405 Method Not Allowed |
| Missing Bearer Token | No `Authorization` header | Returns 401 Unauthorized |
| Invalid Bearer Token | `Authorization: Bearer invalid_token` | Returns 401 Unauthorized |

This ensures comprehensive testing of input validation, edge cases, and boundary conditions.


---

### 1.5 Water Analysis

**URL:** `/api/water-analysis`  
**Content-Type:** `application/json`  
**Method:** `GET`  
**Description:** This endpoint run analysis for specified bbox, date, and analysis type. The supported analysis types are AWEI, NDCI, 
NDTI, SABI, and CDOM. The supported outputs are COG, PNG, and NetCDF. It will return task ID, that user can pool on to check if it is
already finished.

#### Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer <your_token_here>
```

If no token is provided or if the token is invalid, the request will return a `401 Unauthorized` error.

#### Request Parameters

| Parameter          | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| start_date        | Date (YYYY-MM-DD) | required | Dataset start date. |
| end_date          | Date (YYYY-MM-DD) | required | Dataset end date. |
| bbox             | array  | required  | Add a bounding box to filter data for specific areas. |
| resolution | int    | optional | Spatial resolution. Default to 20 |
| calc_types        | list | optional  | Default to all analysis types [AWEI, NDCI, NDTI, SABI, and CDOM] |
| export_plot   | bool  | optional | Export analysis result as PNG plot with style. Default to True. |
| export_nc   | bool  | optional | Export analysis result as NetCDF. Default to True. |
| export_cog   | bool  | optional | Export analysis result as COG. Default to True. |

#### Response Structure

**Success Response (200 OK)**

```json
{
    "message": {
        "task_id": "9e2ae848-f02e-453c-9e10-b59046c44161"
    }
}
```

**Error Response (400 Bad request)**

```json
{
  "status": "error",
  "message": "Invalid bounding box"
}
```

**401 Unauthorized** (When no token is provided or the token is invalid)

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token"
}
```

---

### 1.6 Analysis Task Status

**URL:** `/api/water-analysis/{task_uuid}`  
**Content-Type:** `application/json`  
**Method:** `GET`  
**Description:** This endpoint returns the status of the specified analysis task.

#### Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer <your_token_here>
```

If no token is provided or if the token is invalid, the request will return a `401 Unauthorized` error.

#### Request Parameters

| Parameter          | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| task_uuid        | string | required | UUID of the task |

#### Response Structure

**Success Response (200 OK)**

```json
{
    "uuid": "9e2ae848-f02e-453c-9e10-b59046c44161",
    "task_name": "Water Analysis admin",
    "status": "completed",
    "parameters": {
        "bbox": [
            19.071814670776433,
            -34.10465768253897,
            19.32407544986191,
            -33.954845668837194
        ],
        "end_date": "2025-01-31",
        "export_nc": false,
        "calc_types": [
            "SABI"
        ],
        "export_cog": true,
        "resolution": 20,
        "start_date": "2025-01-01",
        "export_plot": false
    },
    "started_at": "2025-03-20T03:08:39.405125Z",
    "completed_at": "2025-03-20T03:10:40.422969Z",
    "created_at": "2025-03-20T03:08:39.362131Z",
    "task_outputs": [
        {
            "id": 21,
            "file": "http://0.0.0.0:8000/media/2/9e2ae848-f02e-453c-9e10-b59046c44161/SABI_2025_01.tif",
            "size": 4461618,
            "monitoring_type": 4,
            "created_at": "2025-03-20T03:10:40.415636Z"
        }
    ]
}
```

**Error Response (400 Bad request)**

```json
{
  "status": "error",
  "message": "Invalid bounding box"
}
```

**401 Unauthorized** (When no token is provided or the token is invalid)

```json
{
  "status": "error",
  "message": "Missing or invalid authentication token"
}
```

# Authentication API - Token Generation

## Endpoint
`POST /api/auth/token`

## Description
This endpoint generates an authentication token that can be used in subsequent API requests requiring authentication.

## Request
### Headers
- `Content-Type: application/json`

### Body Parameters
| Parameter   | Type   | Required | Description |
|------------|--------|----------|-------------|
| `username` | string | Yes      | The username of the user. |
| `password` | string | Yes      | The password of the user. |
| `grant_type` | string | No | The type of authentication request (e.g., `password`). Default is `password`. |

### Example Request
```json
{
  "username": "user@example.com",
  "password": "securepassword",
  "grant_type": "password"
}
```

## Response
### Success Response
#### Status Code: `200 OK`

| Parameter   | Type   | Description |
|------------|--------|-------------|
| `token`    | string | The generated authentication token. |
| `expires_in` | integer | Token expiration time in seconds. |
| `token_type` | string | Type of token, typically `Bearer`. |

#### Example Response
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### Error Responses
#### Invalid Credentials
**Status Code:** `401 Unauthorized`
```json
{
  "error": "Invalid username or password."
}
```

#### Missing Parameters
**Status Code:** `400 Bad Request`
```json
{
  "error": "Username and password are required."
}
```

## Usage
After obtaining a token, include it in the `Authorization` header for subsequent API requests:
```
Authorization: Bearer {token}
```

## Notes
- The token expires after the duration specified in `expires_in`.
- A new token must be requested once the previous one expires.


