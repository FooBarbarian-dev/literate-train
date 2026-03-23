from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from relations.models import (
    FileStatus,
    FileStatusHistory,
    LogRelationship,
    Relation,
    TagRelationship,
)
from relations.serializers import (
    FileStatusHistorySerializer,
    FileStatusSerializer,
    FileStatusUpsertSerializer,
    LogRelationshipSerializer,
    RelationBulkItemSerializer,
    RelationSerializer,
    TagRelationshipSerializer,
)


# ---------------------------------------------------------------------------
# RelationViewSet
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(summary="List relations"),
    retrieve=extend_schema(summary="Retrieve a relation"),
    create=extend_schema(summary="Create a relation"),
    update=extend_schema(summary="Update a relation"),
    partial_update=extend_schema(summary="Partially update a relation"),
    destroy=extend_schema(summary="Delete a relation"),
)
class RelationViewSet(viewsets.ModelViewSet):
    """CRUD and bulk operations for Relation objects."""

    queryset = Relation.objects.all()
    serializer_class = RelationSerializer
    filterset_fields = [
        "source_type",
        "target_type",
        "pattern_type",
    ]
    search_fields = ["source_value", "target_value"]
    ordering_fields = ["strength", "connection_count", "last_seen", "first_seen"]

    @extend_schema(
        summary="Bulk ingest relations",
        description=(
            "Accept an array of relations and upsert them. "
            "Matching is done on the unique constraint "
            "(source_type, source_value, target_type, target_value)."
        ),
        request=RelationBulkItemSerializer(many=True),
        responses={200: RelationSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="bulk_ingest")
    def bulk_ingest(self, request):
        items = request.data
        if not isinstance(items, list):
            return Response(
                {"detail": "Expected a list of relation objects."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = []
        for item_data in items:
            serializer = RelationBulkItemSerializer(data=item_data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            lookup = {
                "source_type": data["source_type"],
                "source_value": data["source_value"],
                "target_type": data["target_type"],
                "target_value": data["target_value"],
            }

            defaults = {k: v for k, v in data.items() if k not in lookup}

            obj, _created = Relation.objects.update_or_create(
                **lookup, defaults=defaults
            )
            results.append(RelationSerializer(obj).data)

        return Response(results, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get relation graph",
        description=(
            "Return nodes and edges suitable for graph visualization. "
            "Optionally filter by source_type, target_type, or pattern_type."
        ),
        parameters=[
            OpenApiParameter(name="source_type", required=False, type=str),
            OpenApiParameter(name="target_type", required=False, type=str),
            OpenApiParameter(name="pattern_type", required=False, type=str),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "value": {"type": "string"},
                            },
                        },
                    },
                    "edges": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"},
                                "strength": {"type": "integer"},
                                "pattern_type": {"type": "string"},
                            },
                        },
                    },
                },
            }
        },
    )
    @action(detail=False, methods=["get"], url_path="graph")
    def graph(self, request):
        qs = self.get_queryset()

        source_type = request.query_params.get("source_type")
        target_type = request.query_params.get("target_type")
        pattern_type = request.query_params.get("pattern_type")

        if source_type:
            qs = qs.filter(source_type=source_type)
        if target_type:
            qs = qs.filter(target_type=target_type)
        if pattern_type:
            qs = qs.filter(pattern_type=pattern_type)

        nodes: dict[str, dict] = {}
        edges: list[dict] = []

        for rel in qs.iterator():
            src_id = f"{rel.source_type}:{rel.source_value}"
            tgt_id = f"{rel.target_type}:{rel.target_value}"

            if src_id not in nodes:
                nodes[src_id] = {
                    "id": src_id,
                    "type": rel.source_type,
                    "value": rel.source_value,
                }
            if tgt_id not in nodes:
                nodes[tgt_id] = {
                    "id": tgt_id,
                    "type": rel.target_type,
                    "value": rel.target_value,
                }

            edges.append(
                {
                    "source": src_id,
                    "target": tgt_id,
                    "strength": rel.strength,
                    "pattern_type": rel.pattern_type,
                }
            )

        return Response(
            {"nodes": list(nodes.values()), "edges": edges},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# LogRelationshipViewSet
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(summary="List log relationships"),
    retrieve=extend_schema(summary="Retrieve a log relationship"),
    create=extend_schema(summary="Create a log relationship"),
    update=extend_schema(summary="Update a log relationship"),
    partial_update=extend_schema(summary="Partially update a log relationship"),
    destroy=extend_schema(summary="Delete a log relationship"),
)
class LogRelationshipViewSet(viewsets.ModelViewSet):
    """CRUD for LogRelationship plus lookup by log_id."""

    queryset = LogRelationship.objects.all()
    serializer_class = LogRelationshipSerializer
    filterset_fields = ["type", "source_id", "target_id"]
    search_fields = ["relationship", "notes"]
    ordering_fields = ["created_at"]

    @extend_schema(
        summary="Get relationships for a log entry",
        description="Return all LogRelationships where the given log_id appears as source or target.",
        parameters=[
            OpenApiParameter(name="log_id", location="path", required=True, type=int),
        ],
        responses={200: LogRelationshipSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="by_log/(?P<log_id>[0-9]+)")
    def by_log(self, request, log_id=None):
        log_id = int(log_id)
        qs = LogRelationship.objects.filter(Q(source_id=log_id) | Q(target_id=log_id))
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# TagRelationshipViewSet
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(summary="List tag relationships"),
    retrieve=extend_schema(summary="Retrieve a tag relationship"),
    create=extend_schema(summary="Create a tag relationship"),
    update=extend_schema(summary="Update a tag relationship"),
    partial_update=extend_schema(summary="Partially update a tag relationship"),
    destroy=extend_schema(summary="Delete a tag relationship"),
)
class TagRelationshipViewSet(viewsets.ModelViewSet):
    """CRUD for TagRelationship."""

    queryset = TagRelationship.objects.all()
    serializer_class = TagRelationshipSerializer
    filterset_fields = ["source_tag_id", "target_tag_id"]
    ordering_fields = ["correlation_strength", "cooccurrence_count", "last_seen"]


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
    filterset_fields = ["filename", "hostname", "status", "previous_status"]
    search_fields = ["filename", "hostname"]
    ordering_fields = ["timestamp"]
