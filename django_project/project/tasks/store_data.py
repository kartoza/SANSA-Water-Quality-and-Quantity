import json
import os

from datetime import datetime, timedelta
import calendar
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from core.celery import app

from project.models.monitor import AnalysisTask
from project.tasks.analysis import run_analysis

logger = get_task_logger(__name__)

User = get_user_model()


@app.task(name="update_stored_data")
def update_stored_data():
    # Get the current date
    today = datetime.today()

    # Determine last month's year and month
    last_month = today.month - 1 if today.month > 1 else 12
    year = today.year if today.month > 1 else today.year - 1

    # Start date: 1st of last month
    start_date = datetime(year, last_month, 1)

    # End date: Last day of last month
    end_date = datetime(year, last_month, calendar.monthrange(year, last_month)[1])

    parameters = {
        "start_date": start_date,
        "end_date": end_date,
        "bbox": [16.344976, -34.819166, 32.83012, -22.12503],
        "resolution": 20,
        "export_plot": False,
        "export_nc": False,
        "export_cog": True,
        "calc_types": ["AWEI"],
    }
    normalized_parameters = json.loads(json.dumps(parameters, sort_keys=True))

    task = AnalysisTask.objects.filter(
        parameters=parameters,
        status=AnalysisTask.Status.COMPLETED).order_by('-created_at').first()

    admin_username = os.getenv('ADMIN_USERNAME')

    if task:
        return
    else:
        task = AnalysisTask.objects.create(
            parameters=normalized_parameters,
            task_name="Water Analysis",
            created_by=User.objects.get(username=admin_username),
        )
    parameters.update({"task_id": task.uuid.hex})

    result = run_analysis.delay(**parameters)
    task.celery_task_id = result.id
    task.save()
