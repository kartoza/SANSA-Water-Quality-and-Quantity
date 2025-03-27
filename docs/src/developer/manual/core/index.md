# Core Module Overview

The `core` module contains the foundational configuration of the SANSA Water Monitoring Platform. It includes the project’s execution entrypoints, background task framework, project-wide settings, URL routing, and context processors.

---

## Contents

| File / Directory             | Description |
|-----------------------------|-------------|
| `asgi.py`                   | ASGI entrypoint for asynchronous deployments (e.g. Uvicorn, Daphne). |
| `wsgi.py`                   | WSGI entrypoint used by traditional servers (e.g. Gunicorn, uWSGI). |
| `celery.py`                 | Initializes Celery workers and integrates with Django settings and `django-celery-beat`. |
| `context_processors.py`     | Custom Django context processors (e.g., exposing Sentry DSN to templates). |
| `factories.py`              | Defines test data factories (e.g., `UserFactory`) for unit testing. |
| `urls.py`                   | Project-level URL router: connects to API and admin paths. |
| `settings/` (directory)     | Contains all Django settings (e.g., base, dev, prod configs). Should include `base.py`, `local.py`, etc. |

---

## Purpose

The `core` app is not a functional app but the backbone of the Django project. It:

- Manages how the server runs (`asgi`, `wsgi`)
- Coordinates background tasks (`celery`)
- Controls environment-specific configuration (`settings/`)
- Links your API and admin through URLs
- Defines reusable behaviors like template context injection

---
