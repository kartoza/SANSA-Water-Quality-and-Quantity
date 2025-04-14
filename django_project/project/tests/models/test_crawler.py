from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Polygon
from project.models.monitor import Crawler, Province


class CrawlerModelTest(TestCase):
    def setUp(self):
        self.province1 = Province.objects.create(
            name="Province1", bbox=Polygon.from_bbox((0, 0, 1, 1))
        )
        self.province2 = Province.objects.create(
            name="Province2", bbox=Polygon.from_bbox((2, 2, 3, 3))
        )

    def test_create_with_province_only(self):
        crawler = Crawler(name="Test Crawler 1", province=self.province1)
        crawler.save(validate=True)
        self.assertEqual(crawler.bbox, self.province1.bbox)

    def test_create_with_bbox_only(self):
        bbox = Polygon.from_bbox((10, 10, 11, 11))
        crawler = Crawler(name="Test Crawler 2", bbox=bbox)
        crawler.save(validate=True)
        self.assertTrue(crawler.bbox.equals(bbox))

    def test_create_with_both_should_fail(self):
        bbox = Polygon.from_bbox((5, 5, 6, 6))
        crawler = Crawler(name="Test Crawler 3", province=self.province1, bbox=bbox)
        with self.assertRaises(ValidationError):
            crawler.save(validate=True)

    def test_update_only_province(self):
        crawler = Crawler(name="Test Crawler 4", province=self.province1)
        crawler.save(validate=True)
        crawler.province = self.province2
        crawler.save(validate=True)
        self.assertEqual(crawler.bbox, self.province2.bbox)

    def test_update_only_bbox(self):
        crawler = Crawler(name="Test Crawler 5", province=self.province1)
        crawler.save(validate=True)
        new_bbox = Polygon.from_bbox((9, 9, 10, 10))
        crawler.bbox = new_bbox
        crawler.save(validate=True)
        self.assertTrue(crawler.bbox.equals(new_bbox))

    def test_update_both_should_fail(self):
        crawler = Crawler(name="Test Crawler 6", province=self.province1)
        crawler.save(validate=True)
        crawler.province = self.province2
        crawler.bbox = Polygon.from_bbox((9, 9, 10, 10))
        with self.assertRaises(ValidationError):
            crawler.save(validate=True)
    