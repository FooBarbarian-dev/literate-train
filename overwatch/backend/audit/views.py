import json
import os
from datetime import datetime

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from accounts.permissions import IsJWTAuthenticated


AUDIT_DIR = "/app/data/audit"


class AuditEventPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class AuditEventListView(APIView):
    """List audit events from the audit log directory."""
    permission_classes = [IsJWTAuthenticated]

    @extend_schema(
        summary="List audit events",
        tags=["audit"],
        parameters=[
            OpenApiParameter(name="start_date", type=str, required=False, description="Filter start date (ISO 8601)"),
            OpenApiParameter(name="end_date", type=str, required=False, description="Filter end date (ISO 8601)"),
            OpenApiParameter(name="page", type=int, required=False, description="Page number"),
            OpenApiParameter(name="page_size", type=int, required=False, description="Items per page"),
        ],
    )
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        # Parse date filters
        start_dt = None
        end_dt = None
        try:
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
        except (ValueError, TypeError):
            return Response(
                {"error": True, "message": "Invalid date format. Use ISO 8601."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Read audit events from files
        events = []
        if os.path.isdir(AUDIT_DIR):
            for filename in sorted(os.listdir(AUDIT_DIR), reverse=True):
                filepath = os.path.join(AUDIT_DIR, filename)
                if not os.path.isfile(filepath):
                    continue
                try:
                    with open(filepath, "r") as f:
                        content = f.read().strip()
                        if not content:
                            continue
                        # Support both single JSON objects and JSON-lines
                        for line in content.splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                event = json.loads(line)
                                events.append(event)
                            except json.JSONDecodeError:
                                continue
                except (IOError, OSError):
                    continue

        # Apply date filters
        if start_dt or end_dt:
            filtered = []
            for event in events:
                event_ts = event.get("timestamp") or event.get("date") or event.get("created_at")
                if not event_ts:
                    filtered.append(event)
                    continue
                try:
                    event_dt = datetime.fromisoformat(str(event_ts).replace("Z", "+00:00"))
                    if start_dt and event_dt < start_dt:
                        continue
                    if end_dt and event_dt > end_dt:
                        continue
                    filtered.append(event)
                except (ValueError, TypeError):
                    filtered.append(event)
            events = filtered

        # Paginate
        paginator = AuditEventPagination()
        page = paginator.paginate_queryset(events, request)
        if page is not None:
            return paginator.get_paginated_response(page)

        return Response({"events": events, "count": len(events)})
