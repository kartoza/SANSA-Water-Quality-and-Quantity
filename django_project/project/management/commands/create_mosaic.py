import os
import subprocess
import tempfile

from django.core.management.base import BaseCommand
from project.models.monitor import TaskOutput, Crawler
from project.tasks.store_data import generate_mosaic

class Command(BaseCommand):
    help = "Build a VRT mosaic from raster layers and convert it to a COG."

    def handle(self, *args, **options):
        crawler = Crawler.objects.first()
        generate_mosaic(crawler)