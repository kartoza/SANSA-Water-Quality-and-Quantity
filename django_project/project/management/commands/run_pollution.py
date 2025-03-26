import os
from django.core.management.base import BaseCommand
from project.utils.calculations.pollution import PollutionAnalyzer


class Command(BaseCommand):
    help = "Analyze point and non-point source pollution and generate reports"

    def add_arguments(self, parser):
        parser.add_argument("--ndti", required=True, help="Path to NDTI raster")
        parser.add_argument("--ndci", required=True, help="Path to NDCI raster")
        parser.add_argument("--point", required=True, help="Path to point sources shapefile")
        parser.add_argument("--nonpoint", required=True, help="Path to non-point areas shapefile")
        parser.add_argument("--output", default="pollution_reports", help="Directory to save JSON reports")

    def handle(self, *args, **options):
        ndti = options["ndti"]
        ndci = options["ndci"]
        point_sources = options["point"]
        non_point_areas = options["nonpoint"]
        output_dir = options["output"]

        self.stdout.write(self.style.NOTICE("Starting pollution analysis..."))

        analyzer = PollutionAnalyzer(
            ndti_raster=ndti,
            ndci_raster=ndci,
            point_sources=point_sources,
            non_point_areas=non_point_areas,
            output_dir=output_dir,
        )

        analyzer.generate_reports()

        self.stdout.write(self.style.SUCCESS("Pollution analysis complete. Reports saved to:"))
        self.stdout.write(self.style.SUCCESS(os.path.abspath(output_dir)))
