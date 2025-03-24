import os
import logging
from celery.utils.log import get_task_logger
from celery import shared_task
from core.celery import app
from django.core.files import File
from project.models.monitor import (
    AnalysisTask, MonitoringIndicatorType
)
from project.utils.calculations.water_extent import (
    calculate_water_extent_from_tif,
    generate_water_mask_from_tif
)

logger = get_task_logger(__name__)


@app.task(bind=True, name="compute_water_extent_task")
def compute_water_extent_task(
    self,
    task_id,
    bbox,
    spatial_resolution=10,
    input_type="AWEI",
    start_date=None,
    end_date=None,
    threshold=0.0
):
    """
    Celery Task: Compute surface water extent using AWEI output for a given task.
    """
    try:
        task = AnalysisTask.objects.get(uuid=task_id)
    except AnalysisTask.DoesNotExist:
        error_msg = f"Task with id {task_id} does not exist."
        logger.error(error_msg)
        self.update_state(state="FAILURE")
        return {"error": error_msg}

    self.update_state(state="RUNNING")
    task.start()

    try:
        awei_type = MonitoringIndicatorType.Type.AWEI
        awei_output = task.task_outputs.filter(
            monitoring_type__monitoring_indicator_type=awei_type
        ).first()

        if not awei_output:
            raise ValueError("AWEI output not found for this task.")

        result = calculate_water_extent_from_tif(awei_output.file.path, threshold=threshold)

        task.add_log(f"Water surface area calculated: {result['area_km2']} km²")
        task.complete()
        self.update_state(state="SUCCESS")

        return {
            "area_km2": result["area_km2"],
            "task_id": task_id,
            "bbox": bbox,
            "spatial_resolution": spatial_resolution,
            "input_type": input_type,
            "start_date": start_date,
            "end_date": end_date,
            "threshold": threshold,
        }

    except Exception as e:
        error_msg = f"Error computing water extent: {str(e)}"
        logger.error(error_msg)
        task.add_log(error_msg, logging.ERROR)
        task.failed()
        self.update_state(state="FAILURE")
        raise


@app.task(bind=True, name="generate_water_mask_task")
def generate_water_mask_task(
    self,
    task_id,
    bbox,
    spatial_resolution=10,
    input_type="AWEI",
    start_date=None,
    end_date=None,
    threshold=0.0
):
    """
    Celery Task: Generate binary water mask from AWEI output of a task.
    """
    try:
        task = AnalysisTask.objects.get(uuid=task_id)
    except AnalysisTask.DoesNotExist:
        error_msg = f"Task with id {task_id} does not exist."
        logger.error(error_msg)
        self.update_state(state="FAILURE")
        return {"error": error_msg}

    self.update_state(state="RUNNING")
    task.start()

    try:
        # Get AWEI output
        awei_type = MonitoringIndicatorType.Type.AWEI_MASK
        awei_output = task.task_outputs.filter(
            monitoring_type__monitoring_indicator_type=awei_type
        ).first()

        if not awei_output:
            raise ValueError("AWEI output not found for this task.")

        # Generate water mask from AWEI file
        result = generate_water_mask_from_tif(awei_output.file.path, threshold=threshold)
        mask_path = result["mask_path"]

        # Save to TaskOutput
        with open(mask_path, "rb") as f:
            django_file = File(f)
            output = task.task_outputs.create(
                monitoring_type=MonitoringIndicatorType.objects.get(
                    monitoring_indicator_type="AWEI_MASK"
                ),
                size=os.path.getsize(mask_path),
                created_by=task.created_by,
            )
            output.file.save(os.path.basename(mask_path), django_file)

        task.add_log(f"Water mask generated and saved: {output.file.url}")
        task.complete()
        self.update_state(state="SUCCESS")

        return {
            "mask_url": output.file.url,
            "task_id": task_id,
            "bbox": bbox,
            "spatial_resolution": spatial_resolution,
            "input_type": input_type,
            "start_date": start_date,
            "end_date": end_date,
            "threshold": threshold,
        }

    except Exception as e:
        error_msg = f"Error generating water mask: {str(e)}"
        logger.error(error_msg)
        task.add_log(error_msg, logging.ERROR)
        task.failed()
        self.update_state(state="FAILURE")
        raise
