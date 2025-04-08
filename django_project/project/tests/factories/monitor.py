import factory
from factory.django import DjangoModelFactory, FileField
from django.contrib.gis.geos import Polygon
from project.models.monitor import Crawler, MonitoringIndicatorType, AnalysisTask, TaskOutput
from core.factories import UserFactory


class CrawlerFactory(DjangoModelFactory):
    class Meta:
        model = Crawler

    name = factory.Sequence(lambda n: f"Test Crawler {n}")
    description = "Test crawler"
    bbox = "POLYGON((19.0489258702967 -33.94384850125489, 19.0762872733183 -33.94384850125489, 19.0762872733183 -33.90809994227304, 19.0489258702967 -33.90809994227304, 19.0489258702967 -33.94384850125489))"  # noqa
    image_type = Crawler.ImageType.SENTINEL
    created_by = factory.SubFactory(UserFactory)


class MonitoringIndicatorTypeFactory(DjangoModelFactory):
    class Meta:
        model = MonitoringIndicatorType

    name = factory.Sequence(lambda n: f"Indicator {n}")


class AnalysisTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnalysisTask

    task_name = factory.Sequence(lambda n: f"Task {n}")


class TaskOutputFactory(DjangoModelFactory):
    class Meta:
        model = TaskOutput

    task = factory.SubFactory(AnalysisTaskFactory)
    monitoring_type = factory.SubFactory(MonitoringIndicatorTypeFactory)
    period = TaskOutput.AnalysisPeriod.MONTHLY
    observation_date = factory.Faker('date_object')
    bbox = factory.LazyFunction(lambda: Polygon.from_bbox((110, -8, 111, -7)))
    size = 1000
    created_by = factory.SubFactory(UserFactory)
    file = FileField(filename='dummy.tif')
