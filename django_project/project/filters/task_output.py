import django_filters
from django.contrib.gis.geos import Polygon
from project.models.monitor import TaskOutput


class TaskOutputFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name="observation_date", lookup_expr="gte")
    to_date = django_filters.DateFilter(field_name="observation_date", lookup_expr="lte")
    bbox = django_filters.CharFilter(method='filter_bbox')

    class Meta:
        model = TaskOutput
        fields = ['task__uuid', 'monitoring_type__name', 'period']

    def filter_bbox(self, queryset, name, value):
        # Expecting bbox in the format: "minx,miny,maxx,maxy"
        try:
            minx, miny, maxx, maxy = map(float, value.split(","))
            bbox_poly = Polygon.from_bbox((minx, miny, maxx, maxy))
            return queryset.filter(bbox__intersects=bbox_poly)
        except Exception:
            return queryset.none()
