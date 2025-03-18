from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.utils.dateparse import parse_date
import datetime


def compute_water_extent(
        bbox,
        spatial_resolution,
        start_date,
        end_date,
        input_type
        ):
    """
    Calculation of water surface area extent.
    """

    # Validate and parse dates
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    if not start_date or not end_date:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    # Ensure end_date is after start_date
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
        (bbox[2] - bbox[0])  # Longitude difference
        * (bbox[3] - bbox[1])  # Latitude difference
        * spatial_resolution
        * resolution_factor
        / 1000.0  # Convert meters to kilometers
    )

    return {
        "area_km2": round(area_km2, 2),
        "days_observed": days_observed,
        "input_type": input_type,
    }


def generate_water_mask(bbox, spatial_resolution, input_type):
    """
    Generating a water mask URL.
    """
    return f"https://127.0.0.1:8000/awei/water_mask_{input_type}_{spatial_resolution}.tif"


class AWEIWaterExtentView(APIView):
    """
    API to compute the Water Surface Area Extent dynamically.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Query parameters:
        - spatial_resolution: int (meters)
        - start_date: str (YYYY-MM-DD)
        - end_date: str (YYYY-MM-DD)
        - bbox: list of 4 floats [minLon, minLat, maxLon, maxLat]
        - input_type: str ("Landsat" or "Sentinel")
        """
        try:
            spatial_resolution = int(request.query_params.get(
                "spatial_resolution", 30
            ))
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")
            bbox = request.query_params.getlist("bbox")
            input_type = request.query_params.get("input_type", "Landsat")

            # Validate bounding box
            if len(bbox) != 4:
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid bounding box format. Expected 4 values.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Convert bbox to float values
            bbox = [float(coord) for coord in bbox]

            # Validate date format
            if not parse_date(start_date) or not parse_date(end_date):
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if input_type not in ["Landsat", "Sentinel"]:
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid input_type. Must be 'Landsat' or 'Sentinel'.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Compute water extent dynamically
            water_extent_km2 = compute_water_extent(
                bbox, spatial_resolution, start_date, end_date, input_type
            )

            return Response(
                {
                    "status": "success",
                    "data": {"bbox": bbox, "area_km2": water_extent_km2},
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AWEIWaterMaskView(APIView):
    """
    API to generate a Water Mask dynamically.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Query parameters:
        - spatial_resolution: int (meters)
        - start_date: str (YYYY-MM-DD)
        - end_date: str (YYYY-MM-DD)
        - bbox: list of 4 floats [minLon, minLat, maxLon, maxLat]
        - input_type: str ("Landsat" or "Sentinel")
        """
        try:
            spatial_resolution = int(request.query_params.get(
                "spatial_resolution", 30
            ))
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")
            bbox = request.query_params.getlist("bbox")
            input_type = request.query_params.get("input_type", "Landsat")

            if len(bbox) != 4:
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid bounding box format. Expected 4 values.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            bbox = [float(coord) for coord in bbox]

            if not parse_date(start_date) or not parse_date(end_date):
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if input_type not in ["Landsat", "Sentinel"]:
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid input_type. Must be 'Landsat' or 'Sentinel'.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate water mask dynamically
            mask_url = generate_water_mask(
                bbox, spatial_resolution, input_type
            )

            return Response(
                {
                    "status": "success",
                    "data": {
                        "mask_url": mask_url,
                        "bbox": bbox,
                        "spatial_resolution": spatial_resolution,
                        "input_type": input_type,
                        "generated_date": datetime.date.today().isoformat(),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
