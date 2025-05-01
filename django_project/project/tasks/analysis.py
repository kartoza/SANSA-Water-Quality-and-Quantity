import logging
from celery import current_app
from celery.utils.log import get_task_logger
from celery import shared_task
from core.celery import app
from project.utils.calculations.analysis import Analysis
from project.models.monitor import AnalysisTask

logger = get_task_logger(__name__)


def run_analysis(start_date,
                 end_date,
                 bbox=None,
                 resolution=20,
                 export_plot=True,
                 export_nc=True,
                 export_cog=True,
                 calc_types=None,
                 task_id=None,
                 mask_path=None,
                 auto_detect_water=True,
                 image_type='sentinel'):
    """Run calculation."""

    try:
        task = AnalysisTask.objects.get(uuid=task_id)
    except AnalysisTask.DoesNotExist:
        logger.error(f"Task with id {task_id} does not exist.")
        return False

    task.start()
    try:
        calculation = Analysis(
            start_date=start_date,
            end_date=end_date,
            bbox=bbox,
            resolution=resolution,
            export_nc=export_nc,
            export_plot=export_plot,
            export_cog=export_cog,
            calc_types=calc_types,
            task=task,
            mask_path=mask_path,
            auto_detect_water=auto_detect_water,
            image_type=image_type
        )
        calculation.run()
    except Exception as e:
        task.add_log(str(e), logging.ERROR)
        task.failed()
        return False
    else:
        task.complete()
        return True


@app.task(bind=True, name='run_analysis_task')
def run_analysis_task(self,
                      start_date,
                      end_date,
                      bbox=None,
                      resolution=20,
                      export_plot=True,
                      export_nc=True,
                      export_cog=True,
                      calc_types=None,
                      task_id=None,
                      mask_path=None,
                      auto_detect_water=True,
                      image_type='sentinel'):
    """Run calculation."""

    self.update_state(state="RUNNING")

    try:
        task = AnalysisTask.objects.get(uuid=task_id)
    except AnalysisTask.DoesNotExist:
        logger.error(f"Task with id {task_id} does not exist.")
        return False

    task.start()
    try:
        calculation = Analysis(
            start_date=start_date,
            end_date=end_date,
            bbox=bbox,
            resolution=resolution,
            export_nc=export_nc,
            export_plot=export_plot,
            export_cog=export_cog,
            calc_types=calc_types,
            task=task,
            mask_path=mask_path,
            auto_detect_water=auto_detect_water,
            image_type=image_type
        )
        calculation.run()
    except Exception as e:
        task.add_log(str(e), logging.ERROR)
        task.failed()
        self.update_state(state="FAILURE")
        return False
    else:
        task.complete()
        self.update_state(state="SUCCESS")
        return True
