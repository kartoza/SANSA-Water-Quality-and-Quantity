# URL Configuration (`core/urls.py`)

This file defines the root URL configuration for the SANSA Water Monitoring Platform project. It connects app-specific routes and Django’s admin interface.

---

## Purpose

The `urlpatterns` list maps top-level URL patterns to views and app-level routers. It also conditionally serves media files in development mode.

---

## Main Patterns

```python
urlpatterns = [
    path('api/', include('project.urls')),
    path('', admin.site.urls),
]
```

- `api/`: Routes all API endpoints defined in `project/urls.py`
- `/`: Maps the root URL to the Django admin dashboard

---

## Static/Media Files (Development Only)

```python
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- Allows serving uploaded files (e.g., GeoTIFFs, NetCDF) via the development server
- Not used in production (where a web server or CDN should serve media)

---

## Example Result

- `http://localhost:8000/` → Django admin
- `http://localhost:8000/api/monitoring/` → Project API endpoint (if defined)
- `http://localhost:8000/media/output_file.tif` → Served during development

---

## Related Docs

- `project/urls.py`: Defines the API and internal routes for the application
