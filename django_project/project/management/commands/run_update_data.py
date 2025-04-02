from django.core.management.base import BaseCommand
from django.utils import timezone

from project.tasks.store_data import update_stored_data
from project.tasks.analysis import run_analysis
from project.models.monitor import AnalysisTask, TaskOutput


class Command(BaseCommand):
    help = 'Run update data'

    def handle(self, *args, **options):
        update_stored_data()

        # paramaters = {"bbox": [19.02317, -33.949483, 19.083424, -33.903904], "end_date": "2025-03-31", "export_nc": True, "calc_types": ["AWEI"], "export_cog": True, "image_type": "sentinel", "resolution": 20, "start_date": "2025-03-01", "export_plot": False, "auto_detect_water": True}

        # paramaters.update({
        # "calc_types": ["NDCI", "NDTI"],
        # })
        
        # outputs = TaskOutput.objects.filter(task_id='639fec75-c1ef-4243-b648-e3bd5aa95d59')
        # for output in outputs:
        #     new_bbox_polygon = output.bbox
        #     new_bbox_polygon.transform(6933)
        #     breakpoint()
        #     paramaters.update({
        #         "bbox": new_bbox_polygon.extent,
        #         "mask_path": output.file.path,
        #     })
        #     run_analysis(**paramaters)