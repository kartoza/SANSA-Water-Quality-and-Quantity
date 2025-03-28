from django.core.management.base import BaseCommand
from pystac_client import Client
from django.utils import timezone
import pandas as pd

import matplotlib.pyplot as plt
from odc.stac import configure_rio, stac_load
from django_project.project.utils.calculations.monitoring import Calculation


class Command(BaseCommand):
    help = 'This is a custom command that prints a simple message.'

    def handle(self, *args, **options):
        start = timezone.now()

        calculation = Calculation(start_date="2024-01-01",
                                  end_date="2024-01-31",
                                  bbox=[
                                      19.0718146707764333, -34.1046576825389707,
                                      19.3240754498619083, -33.9548456688371942
                                  ],
                                  resolution=10,
                                  export_nc=False)
        calculation.run()

        end = timezone.now()
        runtime = end - start
        runtime.total_seconds()

        print(f"Total runtime: {runtime.total_seconds():.2f} seconds")
