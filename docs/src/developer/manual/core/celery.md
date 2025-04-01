# Celery Configuration (`core/celery.py`)

This module sets up the Celery worker for the SANSA Water Monitoring Platform. Celery is used for asynchronous task execution and scheduled background jobs such as satellite analysis and data ingestion.

---

## Purpose

The `celery.py` file configures:

- **Redis** as the Celery broker
- Integration with Django settings
- Automatic task discovery from all registered apps
- Django admin support for periodic tasks via `django-celery-beat`

---

## How It Works

### 1. Set Django Settings

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
```
Ensures that the Django environment is loaded before Celery starts.

---

### 2. Broker URL Configuration

```python
BASE_REDIS_URL = (
    f'redis://default:{os.environ.get("REDIS_PASSWORD", "")}'
    f'@{os.environ.get("REDIS_HOST", "")}',
)
```

- Uses environment variables to build the Redis broker URL.
- Expected variables:
  - `REDIS_HOST`: Redis server hostname
  - `REDIS_PASSWORD`: (optional) password

---

### 3. Celery App Initialization

```python
app = Celery('sansa-water-quality-and-quantity')
```
The name here matches the project identifier used across tasks.

---

### 4. Settings Integration

```python
app.config_from_object('django.conf:settings', namespace='CELERY')
```
This allows you to define Celery settings in `settings.py` using the `CELERY_` prefix.

Example:
```python
CELERY_TIMEZONE = 'Africa/Johannesburg'
CELERY_TASK_TRACK_STARTED = True
```

---

### 5. Task Autodiscovery

```python
app.autodiscover_tasks()
```
Finds all modules named `tasks.py` in installed apps.

---

### 6. Beat Scheduler

```python
app.conf.beat_scheduler = 'django_celery_beat.schedulers.DatabaseScheduler'
```
This enables recurring tasks to be managed in the Django admin via `django-celery-beat`.

---

## Usage

**Start the worker:**
```bash
celery -A core worker -l info
```

**Start the scheduler (for beat):**
```bash
celery -A core beat -l info
```

---

## Related Tools

- [Django-Celery-Beat](https://github.com/celery/django-celery-beat)
- [Celery Documentation](https://docs.celeryq.dev/en/stable/)
