import json
import os
import calendar

from datetime import date, timedelta
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from core.celery import app
from django.utils import timezone

from project.models.monitor import AnalysisTask, Crawler, TaskOutput, MonitoringIndicatorType
from project.tasks.analysis import run_analysis
from project.utils.helper import get_admin_user


logger = get_task_logger(__name__)

User = get_user_model()


@app.task(name="process_crawler")
def process_crawler(start_date, end_date, crawler):
    bbox = crawler.bbox.extent
    parameters = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "bbox": bbox,
        "resolution": 20,
        "export_plot": False,
        "export_nc": False,
        "export_cog": True,
        "calc_types": ["AWEI"],
        "auto_detect_water": True,
        "image_type": crawler.image_type,
    }
    month = '{:02d}'.format(start_date.month)
    year = start_date.year
    task, _ = AnalysisTask.objects.get_or_create(
        parameters=parameters,
        defaults={
            'task_name': f"Periodic Update {crawler.name} {year}-{month}",
            'created_by': get_admin_user()
        }
    )
    if task.status == AnalysisTask.Status.COMPLETED:
        return
    parameters.update({"task_id": task.uuid.hex})
    # Extract water body
    run_analysis(**parameters)

    # Once done, loop all water body belonging to this task,
    # then calculate NDCI and NDT
    parameters.update({
        "calc_types": ["NDCI", "NDTI"],
    })

    outputs = TaskOutput.objects.filter(
        task=task,
        monitoring_type__name=MonitoringIndicatorType.Type.AWEI
    )
    for output in outputs:
        parameters.update({
            "bbox": output.bbox.extent,
            "mask_path": output.file.path,
        })
        run_analysis(**parameters)


@app.task(name="update_stored_data")
def update_stored_data():
    # Get the current date
    today = timezone.now().today()

    # Determine last month's year and month
    last_month = today.month - 1 if today.month > 1 else 12
    year = today.year if today.month > 1 else today.year - 1

    # Start date: 1st of last month
    start_date = date(year, last_month, 1)

    # End date: Last day of last month
    end_date = date(year, last_month, calendar.monthrange(year, last_month)[1])

    for crawler in Crawler.objects.all():
        process_crawler(start_date, end_date, crawler)
    return {"message": "Task already completed."}
