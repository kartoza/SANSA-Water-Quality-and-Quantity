import json
import logging
import os
import calendar
import geopandas as gpd
from shapely.geometry import box
from copy import deepcopy

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
from project.models.logs import TaskLog
from project.tasks.analysis import run_analysis
from project.utils.helper import get_admin_user


logger = get_task_logger(__name__)

User = get_user_model()


@app.task(
    name="process_water_body",
    bind=True,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def process_water_body(self, parameters, task_id, crawler_progress_id):
    crawler_progress = CrawlProgress.objects.get(id=crawler_progress_id)
    task = AnalysisTask.objects.get(uuid=task_id)
    crawler_progress.increment_processed_data()
    if task.status == Status.COMPLETED:
        self.update_state(state="SUCCESS")

    # Extract water body
    success = run_analysis(**parameters)
    if not success:
        self.update_state(state="FAILURE")
        return

    # Once done, loop all water body belonging to this task,
    # then calculate NDCI and NDT
    parameters.update({
        "calc_types": ["NDCI", "NDTI"],
    })

    outputs = TaskOutput.objects.filter(
        task=task,
        monitoring_type__name=MonitoringIndicatorType.Type.AWEI
    )
    all_success = True
    for output in outputs:
        parameters.update({
            "bbox": output.bbox.extent,
            "mask_path": output.file.path,
        })
        success = run_analysis(**parameters)

        if not success:
            all_success &= False

    if not all_success:
        self.update_state(state="FAILURE")


@app.task(
    name="process_catchment",
    bind=True,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
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

    bbox = crawler.bbox.extent
    # Create a shapely box (rectangle geometry)
    bbox_geom = box(*bbox)

    gdf_waterbodies = gpd.read_file(
        absolute_path('project', 'data', 'sa_waterbodies.gpkg'),
        layer="waterbodies"
    )
    gdf_waterbodies = gdf_waterbodies[gdf_waterbodies.geometry.apply(
        lambda geom: geom.intersects(bbox_geom)
    )].sort_values(by="area_m2", ascending=False)
    crawler_progress = CrawlProgress.objects.create(
        crawler=crawler,
        status=Status.RUNNING,
        started_at=timezone.now(),
    )

    for idx, row in gdf_waterbodies.iterrows():
        parameters = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "bbox": row.geometry.bounds,
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
        task, created = AnalysisTask.objects.get_or_create(
            parameters=parameters,
            defaults={
                'task_name': f"Periodic Update {crawler.name} {row.uid} {year}-{month}",
                'created_by': get_admin_user()
            }
        )

        log_msg = "Crawl Progess {} | Created Analysis Task {}".format(
            crawler_progress.id,
            task.uuid.hex
        )
        skip_task = False
        if not created:
            log_msg = "Crawl Progess {} | Use existing Analysis Task {}".format(
                crawler_progress.id,
                task.uuid.hex
            )
            skip_task = True
            if task.status == Status.COMPLETED:
                log_msg = "Crawl Progess {} | Analysis Task {} is finished".format(
                    crawler_progress.id,
                    task.uuid.hex
                )
                skip_task = True
            elif task.status == Status.RUNNING:
                log_msg = "Crawl Progess {} | Analysis Task {} is running".format(
                    crawler_progress.id,
                    task.uuid.hex
                )

        TaskLog.objects.create(
            content_object=crawler_progress,
            log=log_msg,
            level=logging.INFO,
        )

        if skip_task:
            TaskLog.objects.create(
                content_object=crawler_progress,
                log="Skiping task",
                level=logging.INFO,
            )
            return

        crawler_progress.data_to_process += 1
        crawler_progress.save()
        new_params = deepcopy(parameters)
        new_params.update({
            "task_id": task.uuid.hex,
        })
        result = process_water_body.delay(
            new_params,
            task.uuid.hex,
            crawler_progress.id
        )
        task.celery_task_id = result.id
        task.save()


@app.task(name="update_stored_data",)
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
