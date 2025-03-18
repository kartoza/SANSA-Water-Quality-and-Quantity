from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from project.utils.calculations.monitoring import CalculateMonitoring
from project.models.monitor import ScheduledTask, MonitoringIndicatorType
from project.tasks.calculation import run_calculation


class MonitoringCalculationView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data

        # Mandatory fields
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        bbox = data.get("bbox")

        if not start_date or not end_date or not bbox:
            return Response(
                {"error": "start_date, end_date, and bbox are required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Optional fields with defaults
        resolution = data.get("resolution", 20)
        export_plot = data.get("export_plot", True)
        export_nc = data.get("export_nc", True)
        export_cog = data.get("export_cog", True)
        calc_types = data.get("calc_types")  # Can be None

        task = ScheduledTask.objects.create(
            task_name=f"Monitoring Calculation {self.request.user.username}",
        )

        try:
            calc = run_calculation(
                start_date=start_date,
                end_date=end_date,
                bbox=bbox,
                resolution=resolution,
                export_plot=export_plot,
                export_nc=export_nc,
                export_cog=export_cog,
                calc_types=calc_types,
                task_id=task.id
            ).delay

            return Response(
                {"message": "Calculation started successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
