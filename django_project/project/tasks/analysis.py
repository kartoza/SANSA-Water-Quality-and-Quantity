from celery.utils.log import get_task_logger
from celery import shared_task
from core.celery import app
from project.utils.calculations.analysis import Analysis
from project.models.monitor import AnalysisTask

logger = get_task_logger(__name__)


@app.task(name='run_analysis')
def run_analysis(
    start_date, end_date, bbox, 
    resolution=20, export_plot=True, export_nc=True, 
    export_cog=True, calc_types=None, task_id=None
    ):
    """Run calculation."""
    
    try:
        task = AnalysisTask.objects.get(uuid=task_id)
    except AnalysisTask.DoesNotExist:
        logger.error(f"Task with id {task_id} does not exist.")
        return

    task.start()
    calculation = Analysis(
        start_date=start_date,
        end_date=end_date,
        bbox=bbox,
        resolution=resolution,
        export_nc=export_nc,
        export_plot=export_plot,
        export_cog=export_cog,
        calc_types=calc_types,
        task=task
    )
    calculation.run()
    task.complete()
    # TODO: Implement this task once function to crawl has been implemented.
