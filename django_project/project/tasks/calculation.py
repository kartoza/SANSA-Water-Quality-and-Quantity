from celery.utils.log import get_task_logger
from celery import shared_task
from core.celery import app
from project.utils.calculations.monitoring import CalculateMonitoring
from project.models.monitor import ScheduledTask

logger = get_task_logger(__name__)


@app.task(name='run_calculation')
def run_calculation(
    start_date, end_date, bbox, 
    resolution=20, export_plot=True, export_nc=True, 
    export_cog=True, calc_types=None, task_id=None
    ):
    """Run calculation."""

    try:
        task = ScheduledTask.objects.get(uuid=task_id)
    except ScheduledTask.DoesNotExist:
        logger.error(f"Task with id {task_id} does not exist.")
        return

    calculation = CalculateMonitoring(
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

    logger.info('Updating stored data')
    # TODO: Implement this task once function to crawl has been implemented.
