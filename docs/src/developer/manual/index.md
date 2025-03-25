# Development Guide: Contributing to the `project` Django App

This guide explains how to work within the `project` Django app. It provides a quick reference for adding views, tasks, serializers, and utilities that power the Water Quantity and Quality Monitoring Platform.

---

## App Directory Structure

| Folder | Purpose |
|--------|---------|
| `api_views/` | Contains Django REST Framework API views |
| `models/` | Django ORM models (e.g., AnalysisTask, TaskOutput) |
| `serializers/` | Transforms models to/from JSON for the API |
| `tasks/` | Background processing tasks (via Celery) |
| `utils/` | Custom logic for analysis, masking, etc. |

---

## API Views

Add views to `api_views/`, typically subclassing `APIView`.

**Example**: Creating a view that triggers an analysis.

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from project.tasks.analysis import run_analysis

class WaterAnalysisAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        result = run_analysis.delay(
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            bbox=data.get("bbox"),
            task_id="..."
        )
        return Response({"task_id": result.id})
```

**Register it in `urls.py`:**

```python
from .api_views import example

urlpatterns = [
    path("api/example/", example.ExampleView.as_view()),
]
```

---

## Celery Tasks

Tasks in `tasks/` perform long-running or scheduled background jobs.

**Example**: `run_analysis` task

```python
@app.task(bind=True, name='run_analysis')
def run_analysis(self, start_date, end_date, bbox, ...):
    ...
```

- Updates task state
- Calls `Analysis.run()`
- Logs progress and results to `AnalysisTask`

Use `.delay()` to enqueue:

```python
run_analysis.delay(start_date="2025-02-01", end_date="2025-02-28", ...)
```

---

## Serializers

Serializers live in `serializers/`. They define how model instances are converted to API-friendly data and vice versa.

**Example**: Serialize `TaskOutput` with a full file URL.

```python
class TaskOutputSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    def get_file(self, obj):
        return self.context['request'].build_absolute_uri(obj.file.url)

    class Meta:
        model = TaskOutput
        fields = ['id', 'file', 'size', 'monitoring_type']
```

Use `SerializerMethodField` for custom logic like building absolute URLs or mapping model properties.

---

## Utility Functions

Utility logic for calculations and processing resides in `utils/`.

Common file locations:
- `utils/calculations/analysis.py` — wraps index computation and water mask generation
- `utils/calculations/extract_info.py` — info parsing helpers
- `utils/calculations/monitoring.py` — utilities for reporting or evaluation

**Example usage:**

```python
from project.utils.calculations.analysis import Analysis

result = Analysis(...).run()
```

---

## Testing

- Add tests in `project/tests/`
- Use Django’s test runner
- Test views, tasks, and logic with representative inputs

---

## Related Docs

- [API Reference – Water Analysis](../api/guide/analysis-api.md)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Task Docs](https://docs.celeryq.dev/)