# Model Documentation: Core Data Models

This page documents all the key database models in the SANSA Water Quantity and Quality Monitoring Platform. Each model reflects a table in the PostgreSQL database and plays a critical role in data ingestion, processing, analysis, reporting, or auditing.

---

## Dataset Models

### `DatasetType` (`project_datasettype`)
Classifies datasets by origin:

- `name`: Display label for the type.
- `description`: Optional explanation.
- `dataset_type`: Enum - either `"satellite"` or `"in-situ"`.

Used to group datasets for analytics and interface filtering.

---

### `Dataset` (`project_dataset`)
Structured dataset derived from raw files or external sources.

- `name`: Label for dataset.
- `description`: Optional context.
- `dataset_type`: Foreign key to `DatasetType`.
- `created_at` / `updated_at`: Timestamps for tracking data lineage.

---

## External Data Models

### `ExternalDataSource` (`project_externaldatasource`)
Defines API endpoints for dynamic ingestion.

- `name`: Source name (e.g., OpenWeather API).
- `api_url`: Full URL to API.
- `requires_auth`: Boolean flag.
- `auth_token`: Used if auth is required.
- `request_method`: GET or POST.
- `response_format`: One of JSON, XML, CSV, GeoTIFF.
- `additional_params`: Optional request params (JSON).

Enables plug-and-play external integrations.

---

### `Provider` (`project_provider`)
Organization or system providing raw data.

- `name`: Provider name.
- `description`: Optional notes.

---

### `DataSourceFile` (`project_datasourcefile`)
Represents a raw file received from a provider.

- `dataset`: Dataset this file supports.
- `provider`: Who sent the file.
- `uploaded_at`: Timestamp for when it was added.

---

## Monitoring Models

### `MonitoringIndicatorType` (`project_monitoringindicatortype`)
Enum list of monitoring types:

- AWEI, NDCI, NDTI, SABI, CDOM.
- `monitoring_indicator_type`: Stores enum value.
- `name` / `description`: Display metadata.

---

### `MonitoringIndicator` (`project_monitoringindicator`)
Computed value for a dataset.

- `dataset`: What dataset was used.
- `monitoring_indicator_type`: What was calculated.
- `value`: Float value.
- `generated_at`: Time of computation.

---

### `MonitoringReport` (`project_monitoringreport`)
Downloadable or link-based report from indicator computation.

- `user`: Creator.
- `monitoring_indicator`: What this report is based on.
- `report_link`: Direct URL to report file.

---

## Task Models

### `ScheduledTask` (`project_scheduledtask`)
Background jobs triggered on a schedule.

- `uuid`: Unique ID.
- `status`: pending, running, completed, failed.
- `started_at` / `completed_at`: Timestamps for lifecycle.

---

### `AnalysisTask` (`project_analysistask`)
User-triggered analysis operation.

- `parameters`: JSON object with bbox, date, etc.
- `created_by`: Who triggered it.
- `celery_task_id`: Links to Celery worker task.
- Status helpers: `.start()`, `.complete()`, `.failed()`, `.add_log()`.

---

### `TaskOutput` (`project_taskoutput`)
Generated file from an analysis task.

- `file`: Output file path (GeoTIFF, NetCDF, etc).
- `monitoring_type`: What kind of data it contains.
- `size`: Bytes.
- `created_by`: Uploader/creator.

---

## Logging and Auditing

### `APIUsageLog` (`project_apiusagelog`)
Track every API call:

- `user`: Who made the call.
- `endpoint`: Path accessed.
- `method`: GET, POST, PUT, DELETE.
- `status_code`: HTTP status.
- `requested_at`: Timestamp.

---

### `DataIngestionLog` (`project_dataingestionlog`)
Track outcomes of fetch attempts.

- `api_log`: Associated request.
- `data_source_file`: What was fetched.
- `status`: success or failed.
- `message`: Optional result or error message.

---

### `ErrorLog` (`project_errorlog`)
Captured exception or crash event.

- `api_log` / `task`: Context of failure.
- `module_name`: Source module.
- `error_type`: Type name (e.g., `ValueError`).
- `error_message`: Description.
- `occured_at`: Timestamp.

---

### `TaskLog` (`project_tasklog`)
Stores structured logs using Django’s `GenericForeignKey`.

- `log`: Text.
- `level`: Logging level (int).
- `content_type`: Linked model.
- `object_id`: UUID or ID of instance.

---

### `UserActivityLog` (`project_useractivitylog`)
Audit trail of user actions.

- `user`: Who acted.
- `activity_type`: LOGIN, LOGOUT, DOWNLOAD, etc.
- `timestamp`: When it occurred.

---
