import csv
import io
import json
import os
import uuid
from datetime import datetime, timezone

from django.conf import settings
from django.http import FileResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsJWTAuthenticated
from export.serializers import ExportFilterSerializer
from logs.models import Log


def _get_filtered_queryset(params):
    """Apply common filters to the Log queryset."""
    qs = Log.objects.all().order_by("-timestamp")

    operation_id = params.get("operation_id")
    if operation_id:
        from operations.models import Operation
        op = Operation.objects.filter(id=operation_id).first()
        if op and op.tag_id:
            qs = qs.filter(log_tags__tag_id=op.tag_id).distinct()

    start_date = params.get("start_date")
    if start_date:
        qs = qs.filter(timestamp__gte=start_date)

    end_date = params.get("end_date")
    if end_date:
        qs = qs.filter(timestamp__lte=end_date)

    tag_ids = params.get("tag_ids")
    if tag_ids:
        try:
            ids = [int(tid.strip()) for tid in tag_ids.split(",")]
            qs = qs.filter(log_tags__tag_id__in=ids).distinct()
        except (ValueError, AttributeError):
            pass

    return qs


LOG_EXPORT_FIELDS = [
    "id", "timestamp", "internal_ip", "external_ip", "mac_address",
    "hostname", "domain", "username", "command", "notes", "filename",
    "status", "hash_algorithm", "hash_value", "pid", "analyst",
    "created_at", "updated_at",
]


class ExportJSONView(APIView):
    """Export logs as a JSON file."""
    permission_classes = [IsJWTAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "export"

    @extend_schema(
        parameters=[ExportFilterSerializer],
        summary="Export logs as JSON",
        tags=["export"],
    )
    def get(self, request):
        filter_serializer = ExportFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        qs = _get_filtered_queryset(filter_serializer.validated_data)
        logs = list(qs.values(*LOG_EXPORT_FIELDS))

        # Serialize datetime fields
        for log_entry in logs:
            for key, value in log_entry.items():
                if isinstance(value, datetime):
                    log_entry[key] = value.isoformat()

        # Write to export directory
        export_root = getattr(settings, "EXPORT_ROOT", "/app/data/exports")
        os.makedirs(export_root, exist_ok=True)

        export_filename = f"export_{uuid.uuid4().hex}.json"
        export_path = os.path.join(export_root, export_filename)

        with open(export_path, "w") as f:
            json.dump(logs, f, indent=2, default=str)

        return FileResponse(
            open(export_path, "rb"),
            as_attachment=True,
            filename=export_filename,
            content_type="application/json",
        )


class ExportCSVView(APIView):
    """Export logs as a CSV file."""
    permission_classes = [IsJWTAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "export"

    @extend_schema(
        parameters=[ExportFilterSerializer],
        summary="Export logs as CSV",
        tags=["export"],
    )
    def get(self, request):
        filter_serializer = ExportFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        qs = _get_filtered_queryset(filter_serializer.validated_data)
        logs = list(qs.values(*LOG_EXPORT_FIELDS))

        # Write to export directory
        export_root = getattr(settings, "EXPORT_ROOT", "/app/data/exports")
        os.makedirs(export_root, exist_ok=True)

        export_filename = f"export_{uuid.uuid4().hex}.csv"
        export_path = os.path.join(export_root, export_filename)

        with open(export_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_EXPORT_FIELDS)
            writer.writeheader()
            for log_entry in logs:
                writer.writerow({
                    k: v.isoformat() if isinstance(v, datetime) else v
                    for k, v in log_entry.items()
                })

        return FileResponse(
            open(export_path, "rb"),
            as_attachment=True,
            filename=export_filename,
            content_type="text/csv",
        )
