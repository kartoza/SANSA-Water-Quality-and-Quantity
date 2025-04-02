import factory
from project.models.monitor import Crawler
from core.factories import UserFactory


class CrawlerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Crawler

    name = factory.Sequence(lambda n: f"Test Crawler {n}")
    description = "Test crawler"
    bbox = "POLYGON((19.0489258702967 -33.94384850125489, 19.0762872733183 -33.94384850125489, 19.0762872733183 -33.90809994227304, 19.0489258702967 -33.90809994227304, 19.0489258702967 -33.94384850125489))"  # noqa
    image_type = Crawler.ImageType.SENTINEL
    created_by = factory.SubFactory(UserFactory)
