from django.core.management.base import BaseCommand
from django.utils import timezone

from project.tasks.store_data import update_stored_data
from project.tasks.analysis import run_analysis
from project.models.monitor import AnalysisTask, TaskOutput


class Command(BaseCommand):
    help = 'Run update data'

    def handle(self, *args, **options):
        try:
            update_stored_data()
        except Exception as e:
            print(e)
