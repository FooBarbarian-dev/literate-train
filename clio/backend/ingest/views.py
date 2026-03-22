import csv
import io

from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsJWTAuthenticated
from ingest.serializers import (
    BulkIngestSerializer,
    BulkIngestResultSerializer,
    LogEntryIngestSerializer,
)
from logs.serializers import LogCreateSerializer
from logs.services import create_log_with_encryption


class BulkIngestView(APIView):
    """Bulk import log entries from a JSON array."""
    permission_classes = [IsJWTAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ingest"

    @extend_schema(
        request=BulkIngestSerializer,
        responses={201: BulkIngestResultSerializer},
        summary="Bulk import log entries (JSON)",
        tags=["ingest"],
    )
    def post(self, request):
        serializer = BulkIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        entries = serializer.validated_data["entries"]
        created = 0
        errors = []

        for i, entry_data in enumerate(entries):
            try:
                log_serializer = LogCreateSerializer(data=entry_data)
                log_serializer.is_valid(raise_exception=True)
                create_log_with_encryption(log_serializer, request.user)
                created += 1
            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        return Response(
            {"created": created, "errors": errors},
            status=status.HTTP_201_CREATED,
        )


class CSVIngestView(APIView):
    """Import log entries from a CSV file."""
    permission_classes = [IsJWTAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ingest"

    @extend_schema(
        summary="Import log entries from CSV",
        tags=["ingest"],
    )
    def post(self, request):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response(
                {"error": True, "message": "No CSV file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            decoded = csv_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return Response(
                {"error": True, "message": "File must be UTF-8 encoded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        errors = []

        for i, row in enumerate(reader):
            try:
                # Strip whitespace from keys and values
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k}
                log_serializer = LogCreateSerializer(data=clean_row)
                log_serializer.is_valid(raise_exception=True)
                create_log_with_encryption(log_serializer, request.user)
                created += 1
            except Exception as e:
                errors.append({"row": i + 1, "error": str(e)})

        return Response(
            {"created": created, "errors": errors},
            status=status.HTTP_201_CREATED,
        )
