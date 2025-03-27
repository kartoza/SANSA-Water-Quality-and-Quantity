# Admin Interface Documentation

The Django Admin module provides an interface for managing datasets, data providers, monitoring tasks, logs, and external sources in the SANSA Water Monitoring Platform. This document outlines how each model is represented, filtered, and managed in the admin dashboard.

---

## Dataset Management

### `DatasetTypeAdmin`
Manages classification of dataset types, such as **Satellite** or **In-Situ**.

- **Fields Displayed**: `id`, `name`
- **Search**: By name
- **Use Case**: Helps users define new dataset categories or rename existing ones.

### `DatasetAdmin`
Controls access to structured datasets that are linked to ingestion and analysis pipelines.

- **Fields Displayed**: `id`, `name`, `dataset_type`, `created_at`, `updated_at`
- **Search**: Dataset name
- **Filters**:
  - Dataset type
  - Creation and update dates

---

## External Data Sources

### `ExternalDataSourceAdmin`
Allows configuring dynamic data sources such as REST APIs that ingest water or environmental data.

- **Fieldsets**:
  - *General Information*: `name`, `description`
  - *API Configuration* (collapsible):
    - URL, auth requirements, token, request method (GET/POST), response format (JSON, XML, GeoTIFF, etc.), and additional parameters
- **Display**: `id`, `name`, `api_url`, `requires_auth`, `created_at`
- **Searchable**: By name or URL
- **Filter**: `requires_auth`

---

## System Logs

### `APIUsageLogAdmin`
Tracks usage of backend APIs by authenticated users.

- **Fields**: `user`, `endpoint`, `method`, `status_code`, `requested_at`
- **Searchable**: Endpoint
- **Filterable**: Method type and date

### `DataIngestionLogAdmin`
Keeps records of all data ingestion attempts — successful or failed.

- **Fields**: API call, file ingested, time of fetch, status, and optional message
- **Search**: Filename or message
- **Filters**: Ingestion status, date

### `ErrorLogAdmin`
Displays captured application-level errors.

- **Fields**: Associated API/task, module name, error type/message, and timestamp
- **Filter**: Error type, date

### `UserActivityLogAdmin`
Audits user actions such as login, logout, data download, etc.

- **Fields**: User, action type, timestamp
- **Search**: Username
- **Filter**: Action type, date

### `TaskLogAdmin`
Generic logger tied to any model object using Django’s content type framework.

- **Fields**: Log message, log level, linked object, and timestamp
- **Search**: UUID or log message
- **Filters**: Content type, severity, date

---

## Monitoring Indicators

### `MonitoringIndicatorTypeAdmin`
Manages types of indicators such as:
- AWEI (surface water)
- NDCI (chlorophyll)
- NDTI (turbidity)
- SABI, CDOM

- **Fields**: Name, description, indicator type enum
- **Filters**: Indicator type

### `MonitoringIndicatorAdmin`
View actual computed values from STAC analysis.

- **Fields**: Linked dataset, indicator type, value, timestamp
- **Filters**: Type, date
- **Search**: Indicator name

### `MonitoringReportAdmin`
View/download full reports created from indicators.

- **Fields**: Linked user, indicator, description, time, and download URL
- **Search**: Description, date

---

## Task and Output Management

### `ScheduledTaskAdmin`
Defines recurring tasks like ingestion or batch analysis.

- **Fields**: Task ID, name, status, start and end time
- **Filter**: Status, date

### `AnalysisTaskAdmin`
Admin for analysis jobs triggered via API or UI.

- **Fields**: Task name, status, creator, creation/start/end timestamps
- **Filters**: Status, time
- **Inline**: Related `TaskOutput` files
- **Read-Only Fields**: UUID and timestamps
- **Ordering**: Newest first

### `TaskOutputAdmin`
Access output files such as GeoTIFFs, NetCDFs, PNGs.

- **Fields**: File path, indicator type, task, creator, timestamp
- **Filters**: Indicator type, user
- **Search**: Task name, indicator, username

---

## Data Providers and Files

### `ProviderAdmin`
Manages external organizations or systems that supply datasets.

- **Fields**: Name, created/updated timestamp
- **Searchable**: Provider name

### `DataSourceFileAdmin`
Track individual raw data files linked to a dataset and provider.

- **Fields**: Name, associated dataset, provider, upload time
- **Searchable**: Filename or timestamp

---
