import logging
import os
import calendar
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import geopandas as gpd
from shapely.geometry import box
from copy import deepcopy
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import shutil

from datetime import date
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from core.celery import app
from django.conf import settings
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



# Smart logger that works for both Celery tasks and management commands
def get_logger():
    """
    Get appropriate logger based on context.
    """
    try:
        # Try to get Celery task logger first
        return get_task_logger(__name__)
    except:
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

# Configuration from environment variables
MAX_THREADS = int(os.getenv('MOSAIC_MAX_THREADS', '4'))
BATCH_SIZE = int(os.getenv('MOSAIC_BATCH_SIZE', '500'))
TARGET_CRS = os.getenv('MOSAIC_TARGET_CRS', 'EPSG:6933')

# Thread-safe counter for progress tracking
progress_lock = Lock()


def reproject_single_raster(args):
    """
    Reproject a single raster to target CRS.
    Args: tuple of (input_path, output_path, batch_id, raster_index)
    """
    input_path, output_path, batch_id, raster_index = args
    
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
            print(f"Batch {batch_id}: Failed to reproject raster {raster_index}: {result.stderr}")
            return {
                'success': False,
                'input_path': input_path,
                'batch_id': batch_id,
                'index': raster_index,
                'error': result.stderr
            }
    except subprocess.TimeoutExpired:
        print(f"Batch {batch_id}: Timeout reprojecting raster {raster_index}")
        return {
            'success': False,
            'input_path': input_path,
            'batch_id': batch_id,
            'index': raster_index,
            'error': 'Timeout'
        }
    except Exception as e:
        print(f"Batch {batch_id}: Exception reprojecting raster {raster_index}: {str(e)}")
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
    
    print(f"Batch {batch_id}: Starting reprojection of {len(raster_paths)} rasters using {MAX_THREADS} threads")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit all tasks
        future_to_args = {executor.submit(reproject_single_raster, args): args for args in reproject_args}
        
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
                print(f"Batch {batch_id}: Reprojected {completed}/{len(raster_paths)} rasters")
    
    print(f"Batch {batch_id}: Reprojection complete. Success: {len(successful_paths)}, Failed: {failed_count}")
    return successful_paths


def merge_batch(reprojected_paths, batch_id, temp_dir, monitoring_type_name):
    """
    Merge reprojected rasters in a batch into single raster using VRT approach.
    """
    if not reprojected_paths:
        print(f"Batch {batch_id}: No rasters to merge")
        return None
    
    if len(reprojected_paths) == 1:
        # Only one raster, just rename it
        batch_output = os.path.join(temp_dir, f"batch_result_{monitoring_type_name}_{batch_id}.tif")
        shutil.move(reprojected_paths[0], batch_output)
        return batch_output
    
    batch_output = os.path.join(temp_dir, f"batch_result_{monitoring_type_name}_{batch_id}.tif")
    batch_vrt = os.path.join(temp_dir, f"batch_temp_{monitoring_type_name}_{batch_id}.vrt")
    
    print(f"Batch {batch_id}: Merging {len(reprojected_paths)} reprojected rasters using VRT")
    
    try:
        # Step 1: Create VRT
        vrt_cmd = [
            "gdalbuildvrt",
            "-srcnodata", "nan",
            "-vrtnodata", "nan",
            batch_vrt,
            *reprojected_paths
        ]
        
        vrt_result = subprocess.run(vrt_cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout
        if vrt_result.returncode != 0:
            print(f"Batch {batch_id}: VRT creation failed: {vrt_result.stderr}")
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
        
        translate_result = subprocess.run(translate_cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        if translate_result.returncode == 0:
            print(f"Batch {batch_id}: Merge successful")
            # Clean up VRT file
            try:
                os.remove(batch_vrt)
            except OSError:
                pass
            return batch_output
        else:
            print(f"Batch {batch_id}: Translation failed: {translate_result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"Batch {batch_id}: Merge timeout")
        return None
    except Exception as e:
        print(f"Batch {batch_id}: Merge exception: {str(e)}")
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
            print(f"Batch {batch_id}: Cleaned up temporary files")
        except OSError as e:
            print(f"Batch {batch_id}: Could not clean up temp files: {e}")


def merge_final_batches(batch_results, final_output_path, monitoring_type_name):
    """
    Merge all batch results into final mosaic using VRT approach and create optimized COG.
    """
    if not batch_results:
        print("No batch results to merge into final mosaic")
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
                print(f"Single batch VRT creation failed: {vrt_result.stderr}")
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
            
            translate_result = subprocess.run(translate_cmd, capture_output=True, text=True, timeout=3600)
            
            # Clean up
            try:
                os.remove(temp_vrt)
            except OSError:
                pass
            
            monitoring_type = MonitoringIndicatorType.objects.get(name=monitoring_type_name)
            print('adding mosaic')
            if translate_result.returncode == 0:
                TaskOutput.objects.create(
                    monitoring_type=monitoring_type,
                    observation_date = timezone.now().date().replace(day=1) - relativedelta(months=1),
                    is_mosaic=True,
                    file=final_output_path
                )
                print("Final mosaic created (single batch) as optimized COG")
                return True
            else:
                print(f"Single batch translation failed: {translate_result.stderr}")
                return False
                
        except Exception as e:
            print(f"Single batch processing exception: {str(e)}")
            return False
    
    # Multiple batch results - use VRT approach
    temp_vrt = final_output_path.replace('.tif', '_temp.vrt')
    
    print(f"Merging {len(batch_results)} batch results into final mosaic using VRT")
    
    try:
        # Step 1: Create VRT from all batch results
        vrt_cmd = [
            "gdalbuildvrt",
            "-srcnodata", "nan",
            "-vrtnodata", "nan",
            temp_vrt,
            *batch_results
        ]
        
        vrt_result = subprocess.run(vrt_cmd, capture_output=True, text=True, timeout=600)  # 10 min timeout
        if vrt_result.returncode != 0:
            print(f"Final VRT creation failed: {vrt_result.stderr}")
            return False
        
        print("VRT created successfully, converting to optimized COG...")
        
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
        
        translate_result = subprocess.run(translate_cmd, capture_output=True, text=True, timeout=7200)  # 2 hour timeout
        
        # Clean up VRT file
        try:
            os.remove(temp_vrt)
        except OSError:
            pass
            
        if translate_result.returncode == 0:
            print("Final mosaic merge successful - optimized COG created")
            
            # Optional: Add overviews for better performance
            print("Adding overviews to final COG...")
            overview_cmd = [
                "gdaladdo",
                "-r", "average",
                "--config", "COMPRESS_OVERVIEW", "LZW",
                "--config", "PREDICTOR_OVERVIEW", "2",
                final_output_path,
                "2", "4", "8", "16", "32"
            ]
            
            overview_result = subprocess.run(overview_cmd, capture_output=True, text=True, timeout=1800)
            if overview_result.returncode == 0:
                print("Overviews added successfully")
            else:
                print(f"Overview creation failed (non-critical): {overview_result.stderr}")
            
            return True
        else:
            print(f"Final mosaic translation failed: {translate_result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Final mosaic merge timeout")
        return False
    except Exception as e:
        print(f"Final mosaic merge exception: {str(e)}")
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
        print(f"No rasters provided for {monitoring_type_name}")
        return False
    
    total_rasters = len(raster_paths)
    total_batches = (total_rasters + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division
    
    print(f"Processing {total_rasters} rasters in {total_batches} batches of {BATCH_SIZE}")
    print(f"Using {MAX_THREADS} threads for reprojection, target CRS: {TARGET_CRS}")
    
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
            
            print(f"Processing batch {batch_id + 1}/{total_batches} ({len(batch_raster_paths)} rasters)")
            
            # Reproject batch
            reprojected_paths = reproject_batch(batch_raster_paths, batch_id, temp_dir)
            
            if not reprojected_paths:
                print(f"Batch {batch_id}: No successful reprojections, skipping")
                cleanup_batch_temp_files(batch_id, temp_dir)
                continue
            
            # Merge batch
            batch_result = merge_batch(reprojected_paths, batch_id, temp_dir, monitoring_type_name)
            
            # Clean up individual reprojected files
            cleanup_batch_temp_files(batch_id, temp_dir)
            
            if batch_result:
                batch_results.append(batch_result)
                print(f"Batch {batch_id + 1}/{total_batches} completed successfully")
            else:
                print(f"Batch {batch_id + 1}/{total_batches} failed to merge")
        
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
            print(f"No successful batches for {monitoring_type_name}")
            return False
    
    finally:
        # Clean up temp directory
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory for {monitoring_type_name}")
            except OSError as e:
                print(f"Could not clean up temp directory: {e}")


def generate_mosaic(crawler: Crawler):
    """
    Generate mosaic for current crawler using batched processing.
    """
    # check periodic update task this month,
    # make sure nothing is pending or running
    now = timezone.now()
    tasks = AnalysisTask.objects.filter(
        task_name__startswith=f'Periodic Update {crawler.name}',
        completed_at__month=now.month,
        completed_at__year=now.year,
        status__in=[Status.PENDING, Status.RUNNING]
    )
    if tasks.exists():
        return
    
    print('All Task finished.')
    print(f"Mosaic configuration - Threads: {MAX_THREADS}, Batch size: {BATCH_SIZE}, Target CRS: {TARGET_CRS}")
    
    for monitoring_type in MonitoringIndicatorType.objects.filter(name__in=['NDCI', 'NDTI']):
        print(f'Generating mosaic for {monitoring_type.name}')
        
        # create mosaic for current month
        rasters = TaskOutput.objects.filter(
            created_at__month=now.month,
            created_at__year=now.year,
            monitoring_type=monitoring_type
        )
        raster_paths = [r.file.path for r in rasters if os.path.exists(r.file.path)]
        
        if not raster_paths:
            print(f"No rasters found for {monitoring_type.name}")
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
            print(f"Mosaic generation successful for {monitoring_type.name}")
        else:
            print(f"Mosaic generation failed for {monitoring_type.name}")
            
import os
import subprocess
import tempfile

from django.core.management.base import BaseCommand
from project.models.monitor import TaskOutput, Crawler

class Command(BaseCommand):
    help = "Build a VRT mosaic from raster layers and convert it to a COG."

    def handle(self, *args, **options):
        crawler = Crawler.objects.first()
        generate_mosaic(crawler)
