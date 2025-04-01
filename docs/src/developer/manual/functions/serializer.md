# Serializer Documentation

This section describes the Django REST Framework serializers used in the SANSA Water Monitoring Platform. Serializers convert model instances into JSON representations and vice versa, and handle validation for incoming API requests.

---

## `DatasetTypeSerializer`

A basic serializer for the `DatasetType` model.

### Purpose
- Used to serialize and expose dataset classification types (e.g., Satellite, In-Situ).
- Automatically includes all fields from the model.

```python
class DatasetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetType
        fields = "__all__"
```

---

## `DatasetSerializer`

Serializer for the `Dataset` model. It includes a nested `DatasetTypeSerializer` for full representation of the dataset type.

```python
class DatasetSerializer(serializers.ModelSerializer):
    dataset_type = DatasetTypeSerializer()

    class Meta:
        model = Dataset
        fields = "__all__"
```

### Notes
- The `dataset_type` is fully expanded instead of just showing the foreign key ID.
- Ideal for read-only views or admin APIs.

---

## `TaskOutputSerializer`

Serializes the outputs of an analysis task, including the file URL and its indicator type.

### Custom Fields
- `file`: Absolute URL of the output file, built from the request context.
- `monitoring_type`: Extracted display name of the indicator type.

```python
class TaskOutputSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    monitoring_type = serializers.SerializerMethodField()

    def get_file(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
    
    def get_monitoring_type(self, obj):
        return obj.monitoring_type.monitoring_indicator_type

    class Meta:
        model = TaskOutput
        fields = ['id', 'file', 'size', 'monitoring_type', 'created_at']
```

---

## `AnalysisTaskStatusSerializer`

Provides a full summary of a background analysis task, including related outputs.

- Includes all relevant metadata: task ID, name, status, timestamps, parameters
- Nested field `task_outputs` lists generated result files

```python
class AnalysisTaskStatusSerializer(serializers.ModelSerializer):
    task_outputs = TaskOutputSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisTask
        fields = ['uuid', 'task_name', 'status', 'parameters', 'started_at', 'completed_at', 'created_at', 'task_outputs']
```

---
