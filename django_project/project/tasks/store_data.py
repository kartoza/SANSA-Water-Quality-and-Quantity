import json
import os
import calendar
import geopandas as gpd
from shapely.geometry import box

from datetime import date, timedelta
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from core.celery import app
from django.utils import timezone

from core.settings.utils import absolute_path
from project.models.monitor import (
    AnalysisTask,
    Crawler,
    CrawlProgress,
    TaskOutput,
    MonitoringIndicatorType,
    Status
)
from project.tasks.analysis import run_analysis
from project.utils.helper import get_admin_user


logger = get_task_logger(__name__)

User = get_user_model()


@app.task(name="process_water_body")
def process_water_body(start_date, end_date, bbox, crawler_progress_id, waterbody_uid):
    crawler_progress = CrawlProgress.objects.get(id=crawler_progress_id)
    crawler = crawler_progress.crawler

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
    if task.status == Status.COMPLETED:
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
    crawler_progress.increment_processed_data()


@app.task(name="process_catchment")
def process_catchment(start_date, end_date, geom, crawler_progress, gdf_waterbodies):
    for idx, row in gdf_waterbodies.iterrows():
        process_water_body.delay(
            start_date,
            end_date,
            row.geometry.bounds,
            crawler_progress.id,
            row.uid
            )


@app.task(name="process_crawler")
def process_crawler(start_date, end_date, crawler_id):
    crawler = Crawler.objects.get(id=crawler_id)
    gdf_catchment = gpd.read_file(
        absolute_path('project', 'data', 'catchments.gpkg'),
        layer="catchments"
    )

    bbox = crawler.bbox.extent
    # Create a shapely box (rectangle geometry)
    bbox_geom = box(*bbox)
    gdf_catchment = gdf_catchment[gdf_catchment.geometry.within(bbox_geom)]

    gdf_waterbodies = gpd.read_file(
        absolute_path('project', 'data', 'sa_waterbodies.gpkg'),
        layer="waterbodies"
    )
    gdf_waterbodies = gdf_waterbodies[gdf_waterbodies.geometry.intersects(
        gdf_catchment.geometry.unary_union
        )].sort_values(
        by="area_m2", ascending=False
    )
    crawler_progress = CrawlProgress.objects.create(
        crawler=crawler,
        status=Status.RUNNING,
        data_to_process=len(gdf_waterbodies),
        started_at=timezone.now(),
    )
    for geom in gdf_catchment.geometry:
        process_catchment(start_date, end_date, geom, crawler_progress, gdf_waterbodies)


@app.task(name="update_stored_data")
def update_stored_data(crawler_ids=None):
    """
    Update stored data for all crawlers or a specific crawler.
    """

    # Get the current date
    today = timezone.now().today()

    # Determine last month's year and month
    last_month = today.month - 1 if today.month > 1 else 12
    year = today.year if today.month > 1 else today.year - 1

    # Start date: 1st of last month
    start_date = date(year, last_month, 1)

    # End date: Last day of last month
    end_date = date(year, last_month, calendar.monthrange(year, last_month)[1])

    crawlers = Crawler.objects.all()
    if crawler_ids:
        crawlers = crawlers.filter(id__in=crawler_ids)

    for crawler in crawlers:
        process_crawler.delay(start_date, end_date, crawler.id)
    return {"message": "Task already completed."}
