import csv
import io
import json
from datetime import datetime

from django.http import StreamingHttpResponse
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsJWTAuthenticated
from export.serializers import ExportFilterSerializer
from logs.models import Log


def _resolve_fields(params):
    """Return the ordered list of fields to export.

    If the caller supplied a ``fields`` query param, validate each entry
    against ``LOG_EXPORT_FIELDS`` and return only the recognised ones (in
    the requested order).  Unknown field names are silently ignored so that
    clients don't have to know the exact server-side field list.  If no
    fields are requested, or none of the requested fields are valid, the
    full ``LOG_EXPORT_FIELDS`` list is returned.
    """
    raw = params.get("fields", "")
    if raw:
        requested = [f.strip() for f in raw.split(",") if f.strip()]
        valid = [f for f in requested if f in LOG_EXPORT_FIELDS]
        if valid:
            return valid
    return list(LOG_EXPORT_FIELDS)


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
    """Export logs as a JSON stream."""
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
        fields = _resolve_fields(filter_serializer.validated_data)

        def stream_json():
            yield "["
            first = True
            for row in qs.values(*fields).iterator():
                serialized = {
                    k: v.isoformat() if isinstance(v, datetime) else v
                    for k, v in row.items()
                }
                if not first:
                    yield ","
                first = False
                yield json.dumps(serialized, default=str)
            yield "]"

        response = StreamingHttpResponse(stream_json(), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="export.json"'
        return response


class ExportCSVView(APIView):
    """Export logs as a CSV stream."""
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
        fields = _resolve_fields(filter_serializer.validated_data)

        def stream_csv():
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=fields)
            writer.writeheader()
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            for row in qs.values(*fields).iterator():
                writer.writerow({
                    k: v.isoformat() if isinstance(v, datetime) else v
                    for k, v in row.items()
                })
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        response = StreamingHttpResponse(stream_csv(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="export.csv"'
        return response
