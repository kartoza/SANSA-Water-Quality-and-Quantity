from celery.utils.log import get_task_logger
from celery import shared_task
from core.celery import app

logger = get_task_logger(__name__)


@app.task(name='update_stored_data')
def update_stored_data():
    """Update stored data."""
    logger.info('Updating stored data')
    # TODO: Implement this task once function to crawl has been implemented.
