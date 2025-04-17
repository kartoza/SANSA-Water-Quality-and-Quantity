import os
import logging
from celery.utils.log import get_task_logger
from core.celery import app
from django.core.files import File
from project.models.monitor import (AnalysisTask, MonitoringIndicatorType, TaskOutput)
from project.utils.calculations.water_extent import (calculate_water_extent_from_tif,
                                                     generate_water_mask_from_tif)

logger = get_task_logger(__name__)


def check_awei_output(task):
    """
    Check if AWEI output exists for the given task.
    """
    awei_type = str(MonitoringIndicatorType.Type.AWEI)
    awei_output = (TaskOutput.objects.filter(
        monitoring_type__name__iexact=awei_type,
        task=task).order_by("-created_at").first())
    return awei_output


@app.task(bind=True, name="compute_water_extent_task")
def compute_water_extent_task(self,
                              task_id,
                              bbox,
                              spatial_resolution=10,
                              input_type="AWEI",
                              start_date=None,
                              end_date=None,
                              threshold=0.0):
    """
    Celery Task: Compute surface water extent using AWEI output.
    """
    from project.utils.calculations.analysis import Analysis

    self.update_state(state="RUNNING")
    try:
        task = AnalysisTask.objects.get(uuid=task_id)
    except AnalysisTask.DoesNotExist:
        error_msg = f"Task with id {task_id} does not exist."
        logger.error(error_msg)
        self.update_state(state="FAILURE")
        return {"error": error_msg}
    task.start()

    try:
        awei_output = check_awei_output(task)

        if not awei_output:
            analysis = Analysis(
                start_date=start_date,
                end_date=end_date,
                bbox=bbox,
                resolution=spatial_resolution,
                export_nc=False,
                export_plot=False,
                export_cog=True,
                calc_types=['AWEI'],
                task=task,
                mask_path=None,
                auto_detect_water=False
            )
            analysis.run()

        awei_output = check_awei_output(task)
        if not awei_output:
            raise ValueError("AWEI output not found for this task.")

        result = calculate_water_extent_from_tif(awei_output.file.path, threshold=threshold)

    except Exception as e:
        error_msg = f"Error computing water extent: {str(e)}"
        logger.error(error_msg)
        task.add_log(error_msg, logging.ERROR)
        task.failed()
        self.update_state(state="FAILURE")
        raise
    else:
        task.add_log(f"Water surface area calculated: {result['area_km2']} km²")
        task.complete()
        self.update_state(state="SUCCESS")
    celery_result = {
        "area_km2": float(result["area_km2"])
    }
    return celery_result


@app.task(bind=True, name="generate_water_mask_task")
def generate_water_mask_task(self,
                             task_id,
                             bbox,
                             spatial_resolution=10,
                             input_type="AWEI",
                             start_date=None,
                             end_date=None,
                             threshold=0.0):
    """
    Celery Task: Generate binary water mask from AWEI output of a task.
    """
    self.update_state(state="RUNNING")
    try:
        task = AnalysisTask.objects.get(uuid=task_id)
    except AnalysisTask.DoesNotExist:
        error_msg = f"Task with id {task_id} does not exist."
        logger.error(error_msg)
        self.update_state(state="FAILURE")
        return {"error": error_msg}

    task.start()
    try:
        # Get AWEI output
        awei_type = str(MonitoringIndicatorType.Type.AWEI)
        awei_output = (TaskOutput.objects.filter(
            monitoring_type__name__iexact=awei_type,
            task=task).order_by("-created_at").first())

        if not awei_output:
            raise ValueError("AWEI output not found for this task.")

        # Generate water mask from AWEI file
        result = generate_water_mask_from_tif(awei_output.file.path, threshold=threshold)
        mask_path = result["mask_path"]

        # Save to TaskOutput
        with open(mask_path, "rb") as f:
            django_file = File(f)
            django_file.name = os.path.basename(mask_path)
            output = TaskOutput.objects.create(
                task=task,
                file=django_file,
                monitoring_type=MonitoringIndicatorType.objects.get(
                    monitoring_indicator_type="AWEI_MASK"),
                size=os.path.getsize(mask_path),
                created_by=task.created_by,
            )

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
