import logging
import uuid

import os
import gc
from typing import List, Optional, Generator
from datetime import date
import rasterio
from rasterio.windows import Window
from rasterio.enums import Resampling
import numpy as np
import logging

from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Polygon
from django.db.models import F
from django.contrib.gis.db import models

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from project.models.dataset import Dataset

User = get_user_model()

logger = logging.getLogger(__name__)


class Status(models.TextChoices):
    PENDING = 'pending', _('Pending')
    RUNNING = 'running', _('Running')
    COMPLETED = 'completed', _('Completed')
    FAILED = 'failed', _('Failed')


class MonitoringIndicatorType(models.Model):
    """
    Defines types of monitoring indicators.
    """

    class Type(models.TextChoices):
        AWEI = 'AWEI', _('AWEI')
        AWEI_MASK = 'AWEI_MASK', _('AWEI_MASK')
        NDTI = 'NDTI', _('NDTI')
        NDCI = 'NDCI', _('NDCI')
        SABI = 'SABI', _('SABI')
        CDOM = 'CDOM', _('CDOM')

    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    monitoring_indicator_type = models.CharField(
        choices=[],
        null=True,
        blank=True,
        max_length=25,
    )

    def __str__(self):
        return self.name


class MonitoringIndicator(models.Model):
    """
    Stores monitoring indicators for datasets.
    """
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    monitoring_indicator_type = models.ForeignKey(MonitoringIndicatorType, on_delete=models.CASCADE)
    indicator_name = models.CharField(max_length=100)
    value = models.FloatField(null=True, blank=False)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Monitoring Indicator {self.id} - {self.indicator_name}"


class MonitoringReport(models.Model):
    """
    Stores generated reports on water quality.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    monitoring_indicator = models.ForeignKey(MonitoringIndicator, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now=True)
    report_link = models.URLField()

    def __str__(self):
        return f"Report {self.id} - {self.monitoring_indicator.name}"


class ScheduledTask(models.Model):
    """
    Tracks scheduled background jobs.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    task_name = models.CharField(null=False, blank=False, max_length=100)
    status = models.CharField(choices=Status.choices,
                              null=False,
                              blank=False,
                              max_length=25,
                              default=Status.PENDING)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.task_name


class AnalysisTask(models.Model):
    """
    Tracks analysis tasks.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    task_name = models.CharField(null=False, blank=False, max_length=100)
    status = models.CharField(choices=Status.choices,
                              null=False,
                              blank=False,
                              max_length=25,
                              default=Status.PENDING)
    parameters = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    celery_task_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.task_name

    def start(self):
        self.status = Status.RUNNING
        self.started_at = timezone.now()
        self.save()

    def complete(self):
        self.status = Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def failed(self):
        self.status = Status.FAILED
        self.completed_at = timezone.now()
        self.save()

    def add_log(self, log, level=logging.INFO):
        from project.models.logs import TaskLog

        task_log = TaskLog(
            content_object=self,
            log=log,
            level=level,
        )
        task_log.save()


def output_layer_dir_path(instance, filename):
    """Return upload directory path for Output Layer."""
    if instance.created_by:
        file_path = f'{str(instance.created_by.pk)}/{str(instance.task.uuid)}/'
    else:
        file_path = f'0/{str(instance.task.uuid)}/'
    file_path = file_path + filename
    return file_path


class TaskOutput(models.Model):
    """Output of a task.
    """

    class AnalysisPeriod(models.TextChoices):
        DAILY = 'daily', _('Daily')
        MONTHLY = 'monthly', _('Monthly')

    task = models.ForeignKey(AnalysisTask, related_name='task_outputs', on_delete=models.CASCADE)
    file = models.FileField(upload_to=output_layer_dir_path)
    size = models.BigIntegerField(default=0)
    monitoring_type = models.ForeignKey(MonitoringIndicatorType, on_delete=models.CASCADE)
    period = models.CharField(
        max_length=10,
        choices=AnalysisPeriod.choices,
        default=AnalysisPeriod.MONTHLY,
    )
    observation_date = models.DateField(
        help_text="Date when the observation was taken",
        null=True,
        blank=True
    )
    bbox = models.PolygonField(null=True, blank=True, srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

        
    @classmethod
    def create_mosaic_streaming(
        cls,
        output_path: str,
        monitoring_type: MonitoringIndicatorType,
        memory_limit_mb: int = 1000,  # Maximum memory to use
        tile_size: int = 512,  # Process in tiles
        compress: str = 'lzw'
    ) -> str:
        """
        Create mosaic using streaming approach for large files (500MB+).
        
        This method processes files in small tiles and never loads entire files into memory.
        """
        now = timezone.now()
        queryset = TaskOutput.objects.filter(
            created_at__month=now.month,
            created_at__year=now.year,
            monitoring_type=monitoring_type
        )
        
        if not queryset.exists():
            raise ValueError("No TaskOutput files found matching the criteria")
        
        logger.info(f"Creating streaming mosaic from {queryset.count()} files")
        
        file_paths = [task_output.file.path for task_output in queryset]

        # Validate all files can be opened
        valid_files = cls._validate_raster_files(file_paths)
        if not valid_files:
            raise ValueError("No valid raster files found")
        
        # Get bounds and resolution from all files
        bounds, crs, dtype, nodata, pixel_size, band_count = cls._analyze_input_files(valid_files)
        
        logger.info(f"Mosaic bounds: {bounds}")
        logger.info(f"Pixel size: {pixel_size}")
        
        # Calculate output dimensions
        width = max(1, int(abs(bounds[2] - bounds[0]) / abs(pixel_size[0])))
        height = max(1, int(abs(bounds[3] - bounds[1]) / abs(pixel_size[1])))
        
        logger.info(f"Output dimensions: {width}x{height} pixels")
        
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid output dimensions: {width}x{height}. Check input file bounds and projections.")
        
        # Create output transform
        transform = rasterio.transform.from_bounds(*bounds, width, height)
        
        # Create output profile
        profile = {
            'driver': 'GTiff',
            'dtype': dtype,
            'nodata': nodata,
            'width': width,
            'height': height,
            'count': band_count,
            'crs': crs,
            'transform': transform,
            'compress': compress,
            'tiled': True,
            'blockxsize': min(512, tile_size),
            'blockysize': min(512, tile_size),
        }
        
        # Add BIGTIFF if file will be large
        estimated_size_mb = (width * height * band_count * np.dtype(dtype).itemsize) / (1024 * 1024)
        if estimated_size_mb > 4000:  # 4GB threshold
            profile['BIGTIFF'] = 'YES'
        
        logger.info(f"Estimated output size: {estimated_size_mb:.1f}MB")
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            # Process each band
            for band_idx in range(1, band_count + 1):
                logger.info(f"Processing band {band_idx}/{band_count}")
                
                # Process in tiles
                for tile_window in cls._generate_tiles(width, height, tile_size):
                    logger.debug(f"Processing tile: {tile_window}")
                    
                    # Get tile bounds in the output CRS
                    tile_bounds = rasterio.windows.bounds(tile_window, transform)
                    
                    # Collect data from all input files for this tile
                    tile_data = cls._process_tile(valid_files, tile_bounds, tile_window, 
                                                crs, band_idx, dtype, nodata)
                    
                    if tile_data is not None:
                        dst.write(tile_data, band_idx, window=tile_window)
                    
                    # Force garbage collection after each tile
                    gc.collect()
                    
                    # Check memory usage
                    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                    if memory_usage > memory_limit_mb * 2:
                        logger.warning(f"High memory usage: {memory_usage:.1f}MB")
        
        logger.info(f"Streaming mosaic created: {output_path}")
        return output_path

    @classmethod
    def _validate_raster_files(cls, file_paths: List[str]) -> List[str]:
        """Validate that files can be opened as rasters."""
        valid_files = []
        
        for file_path in file_paths:
            try:
                with rasterio.open(file_path) as src:
                    # Basic validation
                    if src.width > 0 and src.height > 0 and src.count > 0:
                        valid_files.append(file_path)
                    else:
                        logger.warning(f"Invalid raster dimensions in {file_path}")
            except Exception as e:
                logger.warning(f"Cannot open {file_path} as raster: {e}")
                continue
        
        logger.info(f"Validated {len(valid_files)}/{len(file_paths)} raster files")
        return valid_files

    @classmethod
    def _analyze_input_files(cls, file_paths: List[str]) -> tuple:
        """Analyze input files to get common bounds, CRS, dtype, etc."""
        if not file_paths:
            raise ValueError("No valid input files provided")
        
        bounds_list = []
        crs_list = []
        dtype_list = []
        nodata_list = []
        pixel_sizes = []
        band_counts = []
        
        for file_path in file_paths:
            try:
                with rasterio.open(file_path) as src:
                    bounds_list.append(src.bounds)
                    crs_list.append(src.crs)
                    dtype_list.append(src.dtypes[0])
                    nodata_list.append(src.nodata)
                    band_counts.append(src.count)
                    
                    # Get pixel size (resolution)
                    transform = src.transform
                    pixel_sizes.append((abs(transform[0]), abs(transform[4])))
                    
                    logger.debug(f"File {file_path}: bounds={src.bounds}, "
                               f"size={src.width}x{src.height}, crs={src.crs}")
                    
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                continue
        
        if not bounds_list:
            raise ValueError("No valid bounds found in input files")
        
        # Use the most common CRS
        crs = max(set(crs_list), key=crs_list.count) if crs_list else None
        
        # Use the most common dtype
        dtype = max(set(dtype_list), key=dtype_list.count) if dtype_list else 'float32'
        
        # Use the first non-None nodata value
        nodata = next((nd for nd in nodata_list if nd is not None), None)
        
        # Use the finest resolution (smallest pixel size)
        if pixel_sizes:
            min_pixel_x = min(ps[0] for ps in pixel_sizes)
            min_pixel_y = min(ps[1] for ps in pixel_sizes)
            pixel_size = (min_pixel_x, min_pixel_y)
        else:
            pixel_size = (1.0, 1.0)  # Default fallback
        
        # Use maximum band count
        band_count = max(band_counts) if band_counts else 1
        
        # Calculate union of all bounds (in the target CRS)
        if crs:
            # Transform all bounds to the target CRS if needed
            transformed_bounds = []
            for i, bounds in enumerate(bounds_list):
                src_crs = crs_list[i]
                if src_crs != crs:
                    try:
                        # Transform bounds to target CRS
                        left, bottom, right, top = transform_bounds(src_crs, crs, *bounds)
                        transformed_bounds.append((left, bottom, right, top))
                    except Exception as e:
                        logger.warning(f"Could not transform bounds from {src_crs} to {crs}: {e}")
                        transformed_bounds.append(bounds)  # Use original bounds
                else:
                    transformed_bounds.append(bounds)
            
            bounds_list = transformed_bounds
        
        # Calculate union bounds
        min_x = min(b[0] for b in bounds_list)
        min_y = min(b[1] for b in bounds_list)
        max_x = max(b[2] for b in bounds_list)
        max_y = max(b[3] for b in bounds_list)
        
        union_bounds = (min_x, min_y, max_x, max_y)
        
        logger.info(f"Analysis complete - CRS: {crs}, Bounds: {union_bounds}, "
                   f"Pixel size: {pixel_size}, Dtype: {dtype}, Bands: {band_count}")
        
        return union_bounds, crs, dtype, nodata, pixel_size, band_count

    @classmethod
    def _calculate_pixel_size(cls, file_paths: List[str]) -> float:
        """Calculate common pixel size from input files."""
        with rasterio.open(file_paths[0]) as src:
            return abs(src.transform[0])  # Assuming square pixels

    @classmethod
    def _generate_tiles(cls, width: int, height: int, tile_size: int) -> Generator:
        """Generate tile windows for processing."""
        for row in range(0, height, tile_size):
            for col in range(0, width, tile_size):
                # Calculate actual tile size (handle edge tiles)
                tile_width = min(tile_size, width - col)
                tile_height = min(tile_size, height - row)
                
                window = Window(col, row, tile_width, tile_height)
                transform = rasterio.windows.transform(window, 
                    rasterio.transform.from_bounds(0, 0, width, height, width, height))
                
                yield window, transform

    @classmethod
    def _process_tile(cls, file_paths: List[str], tile_bounds: tuple, 
                     tile_window: Window, tile_transform) -> Optional[np.ndarray]:
        """Process a single tile by reading from all overlapping input files."""
        tile_data = None
        
        for file_path in file_paths:
            with rasterio.open(file_path) as src:
                # Check if this file intersects with the tile
                if not cls._bounds_intersect(src.bounds, tile_bounds):
                    continue
                
                try:
                    # Read data for this tile
                    data = src.read(1, 
                        window=rasterio.windows.from_bounds(*tile_bounds, src.transform),
                        out_shape=(tile_window.height, tile_window.width),
                        resampling=Resampling.nearest
                    )
                    
                    if data is not None and not np.all(data == src.nodata):
                        if tile_data is None:
                            tile_data = data.copy()
                        else:
                            # Merge data (you can customize this logic)
                            mask = (data != src.nodata) & (tile_data == src.nodata)
                            tile_data[mask] = data[mask]
                
                except Exception as e:
                    logger.warning(f"Error reading tile from {file_path}: {e}")
                    continue
        
        return tile_data

    @classmethod
    def _bounds_intersect(cls, bounds1: tuple, bounds2: tuple) -> bool:
        """Check if two bounding boxes intersect."""
        return not (bounds1[2] < bounds2[0] or bounds1[0] > bounds2[2] or 
                   bounds1[3] < bounds2[1] or bounds1[1] > bounds2[3])


class Province(models.Model):
    """Stores information about provinces.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    bbox = models.PolygonField(null=True, blank=True, srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='provinces_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='provinces_updated'

    )

    def __str__(self):
        return self.name


class Crawler(models.Model):
    """Stores information about web crawlers.
    """
    class ImageType(models.TextChoices):
        LANDSAT = 'landsat', _('landsat')
        SENTINEL = 'sentinel', _('sentinel')

    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, null=True, blank=True)
    bbox = models.PolygonField(null=True, blank=True, srid=4326)
    image_type = models.CharField(
        choices=ImageType.choices,
        default=ImageType.SENTINEL,
    )
    resolution = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='crawler_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='crawler_updated_by',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self._validate_and_set_bbox()

    def save(self, *args, validate=True, **kwargs):
        if validate:
            self.full_clean()
        return super().save(*args, **kwargs)

    def _validate_and_set_bbox(self):
        """Validate and set province/bbox fields."""
        is_new = self._state.adding

        if is_new:
            if self.province and self.bbox:
                raise ValidationError(
                    "Only one of 'province' or 'bbox' should be set on creation."
                )
            elif self.province:
                self.bbox = self.province.bbox
            elif not self.bbox:
                raise ValidationError(
                    "You must set either 'province' or 'bbox' when creating a Crawler."
                )
        else:
            old = Crawler.objects.get(pk=self.pk)
            province_changed = self.province != old.province
            bbox_changed = self.bbox != old.bbox

            if province_changed and bbox_changed:
                raise ValidationError(
                    "Only one of 'province' or 'bbox' may be changed at a time."
                )
            elif province_changed:
                if self.province:
                    if self.bbox != self.province.bbox:
                        self.bbox = self.province.bbox
                else:
                    raise ValidationError(
                        "Cannot unset province without providing a bbox."
                    )


class CrawlProgress(models.Model):
    """
    Stores progress of a crawler.
    """

    crawler = models.ForeignKey(Crawler, on_delete=models.CASCADE)
    data_to_process = models.IntegerField(default=0)
    processed_data = models.IntegerField(default=0)
    progress = models.FloatField(default=0)
    status = models.CharField(max_length=20, default=Status.PENDING, choices=Status.choices)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Crawl Progress'
        verbose_name_plural = 'Crawl Progresses'

    def __str__(self):
        return f"Crawl Progress for {self.crawler.name}"

    def increment_processed_data(self):
        # Increment processed_data by 1 using F expression
        CrawlProgress.objects.filter(pk=self.pk).update(processed_data=F('processed_data') + 1)

        # Refresh from DB to get the updated value
        self.refresh_from_db(fields=['processed_data', 'data_to_process'])

        # Recalculate progress
        if self.data_to_process > 0:
            self.progress = round(
                (self.processed_data / self.data_to_process) * 100,
                2
            )

        if self.progress >= 100:
            self.status = Status.COMPLETED
            self.completed_at = timezone.now()

        # Save the updated progress
        self.save()

    def save(self, *args, **kwargs):
        if self.data_to_process > 0:
            self.progress = round(
                (self.processed_data / self.data_to_process) * 100,
                2
            )
            if self.progress >= 100:
                self.status = Status.COMPLETED
                self.completed_at = timezone.now()
        super().save(*args, **kwargs)
