import uuid
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from project.models import TaskOutput
from project.tests.factories.monitor import (
    TaskOutputFactory,
    UserFactory,
    MonitoringIndicatorTypeFactory,
    AnalysisTaskFactory,
)


class TaskOutputFilterTestCase(APITestCase):
    """
    Test Case for TaskOutput Filter API.

    This test suite checks:
    - Filtering by task UUID
    - Filtering by monitoring type (ID and name)
    - Filtering by period
    - Filtering by observation date range
    - Filtering by bounding box (bbox)
    - Rejection of unauthenticated access
    """

    def setUp(self):
        """
        Setup initial user and TaskOutput data for filter tests.
        """
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.indicator = MonitoringIndicatorTypeFactory()
        self.task = AnalysisTaskFactory()

        self.task_output = TaskOutputFactory(
            task=self.task,
            monitoring_type=self.indicator,
            period=TaskOutput.AnalysisPeriod.DAILY,
            observation_date="2024-02-02",
            bbox="POLYGON((110 -8, 111 -8, 111 -7, 110 -7, 110 -8))",
            created_by=self.user,
        )

    def get_url(self, **kwargs):
        """
        Build a filtered URL for the task-output-list endpoint.
        """
        base = reverse("task-output-list")
        return base + "?" + "&".join(f"{k}={v}" for k, v in kwargs.items())

    def assert_exist(self, url, expected_count):
        """
        Helper to assert that a given URL returns the expected number of results.
        """
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), expected_count)

    def test_filter_by_task(self):
        """
        Ensure filtering by task UUID returns correct results.
        """
        # Valid task
        url = self.get_url(task__uuid=self.task.uuid)
        self.assert_exist(url, 1)

        # Nonexistent task
        url = self.get_url(task__uuid=uuid.uuid4().hex)
        self.assert_exist(url, 0)

    def test_filter_by_monitoring_type(self):
        """
        Ensure filtering by monitoring_type ID and name works.
        """
        # Filter by ID
        url = self.get_url(monitoring_type=self.indicator.id)
        self.assert_exist(url, 1)

        # Filter by name
        url = self.get_url(monitoring_type__name=self.indicator.name)
        self.assert_exist(url, 1)

        # Filter by non-existent name
        url = self.get_url(monitoring_type__name='non_existing_type')
        self.assert_exist(url, 0)

    def test_filter_by_period(self):
        """
        Ensure filtering by analysis period works.
        """
        # Matching period
        url = self.get_url(period="daily")
        self.assert_exist(url, 1)

        # Non-matching period
        url = self.get_url(period="monthly")
        self.assert_exist(url, 0)

    def test_filter_by_date_range(self):
        """
        Ensure filtering by observation date range works.
        """
        # Matching date range
        url = self.get_url(from_date="2024-02-01", to_date="2024-02-03")
        self.assert_exist(url, 1)

        # Non-matching date range
        url = self.get_url(from_date="2020-02-01", to_date="2020-02-03")
        self.assert_exist(url, 0)

    def test_filter_by_bbox(self):
        """
        Ensure spatial filtering by bbox works.
        """
        # Bounding box that includes the geometry
        url = self.get_url(bbox="110,-8,111,-7")
        self.assert_exist(url, 1)

        # Bounding box that does not intersect
        url = self.get_url(bbox="0,1,0,1")
        self.assert_exist(url, 0)

    def test_unauthenticated_access_denied(self):
        """
        Ensure unauthenticated users are denied access.
        """
        self.client.logout()
        url = reverse("task-output-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
