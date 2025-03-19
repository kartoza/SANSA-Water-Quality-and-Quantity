from rest_framework import serializers
from .models import Dataset, DatasetType


class DatasetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetType
        fields = "__all__"


class DatasetSerializer(serializers.ModelSerializer):
    dataset_type = DatasetTypeSerializer()

    class Meta:
        model = Dataset
        fields = "__all__"
