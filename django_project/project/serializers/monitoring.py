# serializers.py
from rest_framework import serializers
from project.models import AnalysisTask, TaskOutput


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
        fields = [
            'id', 'file', 'size',
            'monitoring_type', 'created_at', 'observation_date',
            'period'
        ]


class AnalysisTaskStatusSerializer(serializers.ModelSerializer):
    task_outputs = TaskOutputSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisTask
        fields = [
            'uuid', 'task_name', 'status', 'parameters', 'started_at', 'completed_at', 'created_at',
            'task_outputs'
        ]
