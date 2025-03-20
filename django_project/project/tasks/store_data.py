from celery.utils.log import get_task_logger
from celery import shared_task
from core.celery import app
from django.utils.dateparse import parse_date
from datetime import datetime

logger = get_task_logger(__name__)


@app.task(name="update_stored_data")
def update_stored_data():
    """Update stored data."""
    logger.info("Updating stored data")
    # TODO: Implement this task once function to crawl has been implemented.


@shared_task
def compute_water_extent_task(
    bbox, spatial_resolution, start_date, end_date, input_type
):
    """
    Celery Task: Computes Water Surface Area asynchronously.
    """

    # Validate dates
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    if not start_date or not end_date:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    days_observed = (end_date - start_date).days
    if days_observed <= 0:
        return {"error": "End date must be after start date."}

    # Validate bounding box
    try:
        bbox = [float(coord) for coord in bbox]
        if len(bbox) != 4:
            return {"error": "Bounding box must contain exactly 4 values."}
    except ValueError:
        return {"error": "Bounding box coordinates must be numeric."}

    # Apply input_type-based scaling factor
    resolution_factor = 1.0 if input_type == "Landsat" else 1.2

    # Compute estimated water surface area
    area_km2 = (
        (bbox[2] - bbox[0])
        * (bbox[3] - bbox[1])
        * spatial_resolution
        * resolution_factor
        / 1000.0
    )

    return {
        "area_km2": round(area_km2, 2),
        "days_observed": days_observed,
        "input_type": input_type,
    }


@shared_task
def generate_water_mask_task(bbox, spatial_resolution, input_type):
    """
    Celery Task: Generates a Water Mask asynchronously.
    """
    try:
        # Validate bounding box
        bbox = [float(coord) for coord in bbox]
        if len(bbox) != 4:
            return {"error": "Bounding box must contain exactly 4 values."}
    except ValueError:
        return {"error": "Bounding box coordinates must be numeric."}

    # Generate water mask URL
    root_url = "https://127.0.0.1:8000"
    mask_url = (
        f"{root_url}/awei/water_mask_{input_type}_{spatial_resolution}.tif"
    )

    return {
        "mask_url": mask_url,
        "bbox": bbox,
        "spatial_resolution": spatial_resolution,
        "input_type": input_type,
        "generated_date": datetime.date()
    }
