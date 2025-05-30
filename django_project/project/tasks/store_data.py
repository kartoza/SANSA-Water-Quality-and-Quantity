import calendar
import geopandas as gpd
import logging
import os
import shutil
import subprocess
from constance import config
from celery.utils.log import get_task_logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import date
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from shapely.geometry import box
from threading import Lock

from core.celery import app
from core.settings.utils import absolute_path
from project.models.logs import TaskLog
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


# Smart logger that works for both Celery tasks and management commands
def get_logger():
    """
    Get appropriate logger based on context.
    """
    try:
        # Try to get Celery task logger first
        return get_task_logger(__name__)
    except Exception:
        # Fall back to standard Python logger for management commands
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            # Add console handler if none exists
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


logger = get_logger()

User = get_user_model()

# Thread-safe counter for progress tracking
progress_lock = Lock()


def reproject_single_raster(args):
    """
    Reproject a single raster to target CRS.
    Args: tuple of (input_path, output_path, batch_id, raster_index)
    """
    input_path, output_path, batch_id, raster_index = args
    TARGET_CRS = config.MOSAIC_TARGET_CRS

    cmd = [
        "gdalwarp",
        "-t_srs", TARGET_CRS,
        "-co", "COMPRESS=DEFLATE",
        "-co", "TILED=YES",
        "-co", "BIGTIFF=IF_SAFER",
        "-overwrite",
        input_path,
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout
        if result.returncode == 0:
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'batch_id': batch_id,
                'index': raster_index
            }
        else:
            logger.error(
                f"Batch {batch_id}: Failed to reproject raster "
                f"{raster_index}: {result.stderr}"
            )
            return {
                'success': False,
                'input_path': input_path,
                'batch_id': batch_id,
                'index': raster_index,
                'error': result.stderr
            }
    except subprocess.TimeoutExpired:
        logger.error(f"Batch {batch_id}: Timeout reprojecting raster {raster_index}")
        return {
            'success': False,
            'input_path': input_path,
            'batch_id': batch_id,
            'index': raster_index,
            'error': 'Timeout'
        }
    except Exception as e:
        logger.error(f"Batch {batch_id}: Exception reprojecting raster {raster_index}: {str(e)}")
        return {
            'success': False,
            'input_path': input_path,
            'batch_id': batch_id,
            'index': raster_index,
            'error': str(e)
        }


def reproject_batch(raster_paths, batch_id, temp_dir):
    """
    Reproject a batch of rasters using threading.
    Returns list of successfully reprojected raster paths.
    """
    batch_temp_dir = os.path.join(temp_dir, f'batch_{batch_id}')
    os.makedirs(batch_temp_dir, exist_ok=True)

    # Prepare arguments for threading
    reproject_args = []
    for i, input_path in enumerate(raster_paths):
        output_filename = f"reprojected_{batch_id}_{i}.tif"
        output_path = os.path.join(batch_temp_dir, output_filename)
        reproject_args.append((input_path, output_path, batch_id, i))

    successful_paths = []
    failed_count = 0

    MAX_THREADS = int(config.MOSAIC_MAX_THREADS)

    logger.info(
        f"Batch {batch_id}: Starting reprojection of {len(raster_paths)} "
        f"rasters using {MAX_THREADS} threads")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit all tasks
        future_to_args = {
            executor.submit(
                reproject_single_raster, args
            ): args for args in reproject_args
        }

        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_args):
            result = future.result()
            completed += 1

            if result['success']:
                successful_paths.append(result['output_path'])
            else:
                failed_count += 1

            # Log progress every 50 completed rasters
            if completed % 50 == 0:
                logger.info(
                    f"Batch {batch_id}: Reprojected "
                    "{completed}/{len(raster_paths)} rasters"
                )

    logger.info(
        f"Batch {batch_id}: Reprojection complete. Success: "
        f"{len(successful_paths)}, Failed: {failed_count}"
    )
    return successful_paths


def merge_batch(reprojected_paths, batch_id, temp_dir, monitoring_type_name):
    """
    Merge reprojected rasters in a batch into single raster using VRT approach.
    """
    if not reprojected_paths:
        logger.info(f"Batch {batch_id}: No rasters to merge")
        return None

    if len(reprojected_paths) == 1:
        # Only one raster, just rename it
        batch_output = os.path.join(temp_dir, f"batch_result_{monitoring_type_name}_{batch_id}.tif")
        shutil.move(reprojected_paths[0], batch_output)
        return batch_output

    batch_output = os.path.join(temp_dir, f"batch_result_{monitoring_type_name}_{batch_id}.tif")
    batch_vrt = os.path.join(temp_dir, f"batch_temp_{monitoring_type_name}_{batch_id}.vrt")

    logger.info(f"Batch {batch_id}: Merging {len(reprojected_paths)} reprojected rasters using VRT")

    try:
        # Step 1: Create VRT
        vrt_cmd = [
            "gdalbuildvrt",
            "-srcnodata", "nan",
            "-vrtnodata", "nan",
            batch_vrt,
            *reprojected_paths
        ]

        vrt_result = subprocess.run(
            vrt_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )  # 5 min timeout
        if vrt_result.returncode != 0:
            logger.error(f"Batch {batch_id}: VRT creation failed: {vrt_result.stderr}")
            return None

        # Step 2: Convert VRT to optimized COG
        translate_cmd = [
            "gdal_translate",
            "-of", "GTiff",
            "-co", "COMPRESS=LZW",
            "-co", "PREDICTOR=2",
            "-co", "TILED=YES",
            "-co", "BIGTIFF=IF_SAFER",
            "-co", "BLOCKXSIZE=512",
            "-co", "BLOCKYSIZE=512",
            batch_vrt,
            batch_output
        ]

        translate_result = subprocess.run(
            translate_cmd,
            capture_output=True,
            text=True,
            timeout=1800
        )  # 30 min timeout
        if translate_result.returncode == 0:
            logger.info(f"Batch {batch_id}: Merge successful")
            # Clean up VRT file
            try:
                os.remove(batch_vrt)
            except OSError:
                pass
            return batch_output
        else:
            logger.error(f"Batch {batch_id}: Translation failed: {translate_result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        logger.info(f"Batch {batch_id}: Merge timeout")
        return None
    except Exception as e:
        logger.info(f"Batch {batch_id}: Merge exception: {str(e)}")
        return None
    finally:
        # Clean up VRT file if it exists
        if os.path.exists(batch_vrt):
            try:
                os.remove(batch_vrt)
            except OSError:
                pass


def cleanup_batch_temp_files(batch_id, temp_dir):
    """
    Clean up individual reprojected files for a batch.
    """
    batch_temp_dir = os.path.join(temp_dir, f'batch_{batch_id}')
    if os.path.exists(batch_temp_dir):
        try:
            shutil.rmtree(batch_temp_dir)
            logger.info(f"Batch {batch_id}: Cleaned up temporary files")
        except OSError as e:
            logger.info(f"Batch {batch_id}: Could not clean up temp files: {e}")


def merge_final_batches(batch_results, final_output_path, monitoring_type_name):
    """
    Merge all batch results into final mosaic using VRT approach and create optimized COG.
    """
    if not batch_results:
        logger.info("No batch results to merge into final mosaic")
        return False

    if len(batch_results) == 1:
        # Only one batch result, convert to optimized COG
        temp_vrt = final_output_path.replace('.tif', '_temp.vrt')

        try:
            # Create VRT from single file
            vrt_cmd = [
                "gdalbuildvrt",
                "-srcnodata", "nan",
                "-vrtnodata", "nan",
                temp_vrt,
                batch_results[0]
            ]

            vrt_result = subprocess.run(vrt_cmd, capture_output=True, text=True, timeout=300)
            if vrt_result.returncode != 0:
                logger.error(f"Single batch VRT creation failed: {vrt_result.stderr}")
                return False

            # Convert to optimized COG
            translate_cmd = [
                "gdal_translate",
                "-of", "GTiff",
                "-co", "COMPRESS=LZW",
                "-co", "PREDICTOR=2",
                "-co", "TILED=YES",
                "-co", "BIGTIFF=IF_SAFER",
                "-co", "BLOCKXSIZE=512",
                "-co", "BLOCKYSIZE=512",
                "-co", "COPY_SRC_OVERVIEWS=YES",
                temp_vrt,
                final_output_path
            ]

            translate_result = subprocess.run(
                translate_cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )

            # Clean up
            try:
                os.remove(temp_vrt)
            except OSError:
                pass

            if translate_result.returncode == 0:
                logger.info("Final mosaic created (single batch) as optimized COG")
                return True
            else:
                logger.error(f"Single batch translation failed: {translate_result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Single batch processing exception: {str(e)}")
            return False

    # Multiple batch results - use VRT approach
    temp_vrt = final_output_path.replace('.tif', '_temp.vrt')

    logger.info(f"Merging {len(batch_results)} batch results into final mosaic using VRT")

    try:
        # Step 1: Create VRT from all batch results
        vrt_cmd = [
            "gdalbuildvrt",
            "-srcnodata", "nan",
            "-vrtnodata", "nan",
            temp_vrt,
            *batch_results
        ]

        vrt_result = subprocess.run(
            vrt_cmd,
            capture_output=True,
            text=True,
            timeout=600
        )  # 10 min timeout
        if vrt_result.returncode != 0:
            logger.error(f"Final VRT creation failed: {vrt_result.stderr}")
            return False

        logger.info("VRT created successfully, converting to optimized COG...")

        # Step 2: Convert VRT to optimized COG with maximum compression
        translate_cmd = [
            "gdal_translate",
            "-of", "GTiff",
            "-co", "COMPRESS=LZW",
            "-co", "PREDICTOR=2",
            "-co", "TILED=YES",
            "-co", "BIGTIFF=IF_SAFER",
            "-co", "BLOCKXSIZE=512",
            "-co", "BLOCKYSIZE=512",
            "-co", "COPY_SRC_OVERVIEWS=YES",
            temp_vrt,
            final_output_path
        ]

        translate_result = subprocess.run(
            translate_cmd,
            capture_output=True,
            text=True,
            timeout=7200
        )  # 2 hour timeout

        # Clean up VRT file
        try:
            os.remove(temp_vrt)
        except OSError:
            pass

        if translate_result.returncode == 0:
            logger.info("Final mosaic merge successful - optimized COG created")

            # Optional: Add overviews for better performance
            logger.info("Adding overviews to final COG...")
            overview_cmd = [
                "gdaladdo",
                "-r", "average",
                "--config", "COMPRESS_OVERVIEW", "LZW",
                "--config", "PREDICTOR_OVERVIEW", "2",
                final_output_path,
                "2", "4", "8", "16", "32"
            ]

            overview_result = subprocess.run(
                overview_cmd,
                capture_output=True,
                text=True,
                timeout=1800
                )
            if overview_result.returncode == 0:
                logger.info("Overviews added successfully")
            else:
                logger.error(f"Overview creation failed (non-critical): {overview_result.stderr}")

            return True
        else:
            logger.error(f"Final mosaic translation failed: {translate_result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.info("Final mosaic merge timeout")
        return False
    except Exception as e:
        logger.info(f"Final mosaic merge exception: {str(e)}")
        return False
    finally:
        # Clean up VRT file if it exists
        if os.path.exists(temp_vrt):
            try:
                os.remove(temp_vrt)
            except OSError:
                pass


def generate_mosaic_batched(raster_paths, monitoring_type_name, final_output_path):
    """
    Generate mosaic using batched reprojection and merging.
    """
    if not raster_paths:
        logger.info(f"No rasters provided for {monitoring_type_name}")
        return False

    MAX_THREADS = int(config.MOSAIC_MAX_THREADS)
    BATCH_SIZE = int(config.MOSAIC_BATCH_SIZE)
    TARGET_CRS = config.MOSAIC_TARGET_CRS
    total_rasters = len(raster_paths)
    total_batches = (total_rasters + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division

    logger.info(f"Processing {total_rasters} rasters in {total_batches} batches of {BATCH_SIZE}")
    logger.info(f"Using {MAX_THREADS} threads for reprojection, target CRS: {TARGET_CRS}")

    # Create temporary directory
    temp_dir = os.path.join(settings.MEDIA_ROOT, f'temp_mosaic_{monitoring_type_name}')
    os.makedirs(temp_dir, exist_ok=True)

    batch_results = []

    try:
        # Process each batch
        for batch_id in range(total_batches):
            start_idx = batch_id * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total_rasters)
            batch_raster_paths = raster_paths[start_idx:end_idx]

            logger.info(
                f"Processing batch {batch_id + 1}/{total_batches} "
                f"({len(batch_raster_paths)} rasters)"
            )

            # Reproject batch
            reprojected_paths = reproject_batch(batch_raster_paths, batch_id, temp_dir)

            if not reprojected_paths:
                logger.info(f"Batch {batch_id}: No successful reprojections, skipping")
                cleanup_batch_temp_files(batch_id, temp_dir)
                continue

            # Merge batch
            batch_result = merge_batch(reprojected_paths, batch_id, temp_dir, monitoring_type_name)

            # Clean up individual reprojected files
            cleanup_batch_temp_files(batch_id, temp_dir)

            if batch_result:
                batch_results.append(batch_result)
                logger.info(f"Batch {batch_id + 1}/{total_batches} completed successfully")
            else:
                logger.error(f"Batch {batch_id + 1}/{total_batches} failed to merge")

        # Merge all batch results into final mosaic
        if batch_results:
            success = merge_final_batches(batch_results, final_output_path, monitoring_type_name)

            if success:
                # Clean up batch results
                for batch_result in batch_results:
                    try:
                        if os.path.exists(batch_result):
                            os.remove(batch_result)
                    except OSError:
                        pass

            return success
        else:
            logger.info(f"No successful batches for {monitoring_type_name}")
            return False

    finally:
        # Clean up temp directory
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory for {monitoring_type_name}")
            except OSError as e:
                logger.info(f"Could not clean up temp directory: {e}")


def generate_mosaic(crawler: Crawler):
    """
    Generate mosaic for current crawler using batched processing.
    """
    # check periodic update task this month,
    # make sure nothing is pending or running
    now = timezone.now()
    MAX_THREADS = int(config.MOSAIC_MAX_THREADS)
    BATCH_SIZE = int(config.MOSAIC_BATCH_SIZE)
    TARGET_CRS = config.MOSAIC_TARGET_CRS
    tasks = AnalysisTask.objects.filter(
        task_name__startswith=f'Periodic Update {crawler.name}',
        completed_at__month=now.month,
        completed_at__year=now.year,
        status__in=[Status.PENDING, Status.RUNNING]
    )
    if tasks.exists():
        return

    logger.info('All Task finished.')
    logger.info(
        f"Mosaic configuration - Threads: {MAX_THREADS}, "
        f"Batch size: {BATCH_SIZE}, Target CRS: {TARGET_CRS}"
    )

    for monitoring_type in MonitoringIndicatorType.objects.all():
        logger.info(f'Generating mosaic for {monitoring_type.name}')

        # create mosaic for current month
        rasters = TaskOutput.objects.filter(
            created_at__month=now.month,
            created_at__year=now.year,
            monitoring_type=monitoring_type
        )
        raster_paths = [r.file.path for r in rasters if os.path.exists(r.file.path)]

        if not raster_paths:
            logger.info(f"No rasters found for {monitoring_type.name}")
            continue

        raster_sample = rasters.first()
        year = raster_sample.observation_date.year
        month = raster_sample.observation_date.strftime('%m')
        output_dir = os.path.join(
            settings.MEDIA_ROOT,
            f'mosaics/{monitoring_type.name}/{year}/{month}'
        )
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(
            output_dir,
            f'SA_{monitoring_type.name}_{year}-{month}.tif'
        )

        # Generate mosaic using batched approach
        success = generate_mosaic_batched(raster_paths, monitoring_type.name, output_path)

        if success:
            logger.info(f"Mosaic generation successful for {monitoring_type.name}")
        else:
            logger.error(f"Mosaic generation failed for {monitoring_type.name}")


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
    logger.info('Run AWEI')
    success = run_analysis(**parameters)
    if not success:
        self.update_state(state="FAILURE")
        return

    # Once done, loop all water body belonging to this task,
    # then calculate NDCI and NDT
    logger.info('Run NDTI, NDCI')
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

    logger.info('Generate Mosaic')
    generate_mosaic(crawler_progress.crawler)


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
