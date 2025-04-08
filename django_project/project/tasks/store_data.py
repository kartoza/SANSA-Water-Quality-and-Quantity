import json
import os
import calendar
import geopandas
import geopandas as gpd
from shapely.geometry import box

from datetime import date, timedelta
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from core.celery import app
from django.utils import timezone

from core.settings.utils import absolute_path
from project.models.monitor import AnalysisTask, Crawler, TaskOutput, MonitoringIndicatorType
from project.tasks.analysis import run_analysis
from project.utils.helper import get_admin_user


logger = get_task_logger(__name__)

User = get_user_model()


@app.task(name="process_water_bocy")
def process_water_body(start_date, end_date, bbox, crawler_id, waterbody_uid):
    crawler = Crawler.objects.get(id=crawler_id)
    parameters = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "bbox": bbox,
        "resolution": crawler.resolution,
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
            'task_name': f"Periodic Update {crawler.name} {waterbody_uid} {year}-{month}",
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

@app.task(name="process_catchment")
def process_catchment(start_date, end_date, geom, crawler):
    gdf = gpd.read_file(absolute_path('project', 'data', 'sa_waterbodies.gpkg'), layer="waterbodies")
    filtered = gdf[gdf.geometry.within(geom)].sort_values(by="area_m2", ascending=False)
    for idx, row in filtered.iterrows():
        # breakpoint()
        process_water_body.delay(start_date, end_date, row.geometry.bounds, crawler.id, row.uid)


@app.task(name="process_crawler")
def process_crawler(start_date, end_date, crawler):
    gdf = gpd.read_file(absolute_path('project', 'data', 'catchments.gpkg'), layer="catchments")

    bbox = crawler.bbox.extent
    # Create a shapely box (rectangle geometry)
    bbox_geom = box(*bbox)
    filtered = gdf[gdf.geometry.within(bbox_geom)]
    for geom in filtered.geometry:
        # process_catchment.delay(start_date, end_date, geom.bounds, crawler)
        process_catchment(start_date, end_date, geom, crawler)


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
