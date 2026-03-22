from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from file_tracking.serializers import (
    FileStatusHistorySerializer,
    FileStatusSerializer,
    FileStatusUpsertSerializer,
)
from relations.models import FileStatus, FileStatusHistory


# ---------------------------------------------------------------------------
# FileStatusViewSet
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(summary="List file statuses"),
    retrieve=extend_schema(summary="Retrieve a file status"),
    create=extend_schema(summary="Create a file status"),
    update=extend_schema(summary="Update a file status"),
    partial_update=extend_schema(summary="Partially update a file status"),
    destroy=extend_schema(summary="Delete a file status"),
)
class FileStatusViewSet(viewsets.ModelViewSet):
    """CRUD for FileStatus with upsert and history actions."""

    queryset = FileStatus.objects.all()
    serializer_class = FileStatusSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["filename", "hostname", "status", "hash_value", "internal_ip"]
    search_fields = ["filename", "hostname", "username", "analyst"]
    ordering_fields = ["first_seen", "last_seen", "filename"]

    @extend_schema(
        summary="Upsert a file status",
        description=(
            "Create or update a FileStatus entry keyed on "
            "(filename, hostname, internal_ip). If the status changes, "
            "a FileStatusHistory record is created automatically."
        ),
        request=FileStatusUpsertSerializer,
        responses={200: FileStatusSerializer, 201: FileStatusSerializer},
    )
    @action(detail=False, methods=["post"], url_path="upsert")
    def upsert(self, request):
        serializer = FileStatusUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lookup = {
            "filename": data["filename"],
            "hostname": data.get("hostname", ""),
            "internal_ip": data.get("internal_ip", ""),
        }
        defaults = {k: v for k, v in data.items() if k not in lookup}

        try:
            existing = FileStatus.objects.get(**lookup)
        except FileStatus.DoesNotExist:
            existing = None

        if existing is not None:
            previous_status = existing.status
            for attr, value in defaults.items():
                setattr(existing, attr, value)
            existing.save()
            obj = existing
            http_status = status.HTTP_200_OK

            new_status = defaults.get("status", previous_status)
            if new_status != previous_status:
                FileStatusHistory.objects.create(
                    filename=obj.filename,
                    status=new_status,
                    previous_status=previous_status,
                    hash_algorithm=obj.hash_algorithm,
                    hash_value=obj.hash_value,
                    hostname=obj.hostname,
                    internal_ip=obj.internal_ip,
                    external_ip=obj.external_ip,
                    mac_address=obj.mac_address,
                    username=obj.username,
                    analyst=obj.analyst,
                    notes=obj.notes,
                    command=obj.command,
                    secrets=obj.secrets,
                    metadata=obj.metadata,
                    operation_tags=obj.operation_tags,
                    source_log_ids=obj.source_log_ids,
                )
        else:
            obj = FileStatus.objects.create(**data)
            http_status = status.HTTP_201_CREATED

        return Response(FileStatusSerializer(obj).data, status=http_status)

    @extend_schema(
        summary="Get history for a file status",
        description="Return all FileStatusHistory records matching the file's filename and hostname.",
        responses={200: FileStatusHistorySerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        file_status = self.get_object()
        qs = FileStatusHistory.objects.filter(
            filename=file_status.filename,
            hostname=file_status.hostname,
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = FileStatusHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = FileStatusHistorySerializer(qs, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# FileStatusHistoryViewSet
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(summary="List file status history"),
    retrieve=extend_schema(summary="Retrieve a file status history entry"),
)
class FileStatusHistoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only viewset for FileStatusHistory."""

    queryset = FileStatusHistory.objects.all()
    serializer_class = FileStatusHistorySerializer
    permission_classes = [AllowAny]
    filterset_fields = ["filename", "hostname", "status", "previous_status"]
    search_fields = ["filename", "hostname"]
    ordering_fields = ["timestamp"]
