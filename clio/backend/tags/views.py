from django.db import models
from django.db.models import Count, Max
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from accounts.permissions import IsJWTAuthenticated, IsAdmin
from tags.models import Tag, LogTag
from tags.serializers import TagSerializer, TagCreateSerializer, TagStatsSerializer, LogTagSerializer
from tags.services import is_operation_tag, get_or_create_tag, add_tag_to_log, remove_tag_from_log


@extend_schema_view(
    list=extend_schema(summary="List all tags", tags=["tags"]),
    create=extend_schema(summary="Create a tag (admin only)", tags=["tags"]),
    retrieve=extend_schema(summary="Get a tag", tags=["tags"]),
    update=extend_schema(summary="Update a tag (admin only)", tags=["tags"]),
    partial_update=extend_schema(summary="Partially update a tag", tags=["tags"]),
    destroy=extend_schema(summary="Delete a tag (admin only)", tags=["tags"]),
)
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsJWTAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return TagCreateSerializer
        return TagSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAdmin()]
        return [IsJWTAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    def perform_update(self, serializer):
        tag = self.get_object()
        if is_operation_tag(tag):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Operation tags cannot be modified")
        serializer.save()

    def perform_destroy(self, instance):
        if is_operation_tag(instance):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Operation tags cannot be deleted")
        instance.delete()

    @extend_schema(summary="Get tag statistics", tags=["tags"])
    @action(detail=False, methods=["get"])
    def stats(self, request):
        tags = Tag.objects.annotate(
            usage_count=Count("log_tags"),
            last_used=Max("log_tags__tagged_at"),
        ).order_by("-usage_count")
        serializer = TagStatsSerializer(tags, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Autocomplete tags", tags=["tags"])
    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response([])
        tags = Tag.objects.filter(name__icontains=query).order_by(
            # Exact match first
            models.Case(
                models.When(name=query.lower(), then=0),
                default=1,
                output_field=models.IntegerField(),
            ),
            models.functions.Length("name"),
            "name",
        )[:20]
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Add or remove a tag on a log", tags=["tags"])
    @action(detail=False, methods=["post", "delete"], url_path="log-tag")
    def log_tag(self, request):
        log_id = request.data.get("log_id")

        if not log_id:
            return Response({"error": True, "message": "log_id required"}, status=400)

        if request.method == "POST":
            tag_id = request.data.get("tag_id")
            tag_name = request.data.get("tag_name")

            if tag_name and not tag_id:
                tag = get_or_create_tag(tag_name, request.user.username)
                tag_id = tag.id

            if not tag_id:
                return Response({"error": True, "message": "tag_id or tag_name required"}, status=400)

            log_tag = add_tag_to_log(log_id, tag_id, request.user.username)
            return Response(LogTagSerializer(log_tag).data, status=201)

        # DELETE
        tag_id = request.data.get("tag_id")
        if not tag_id:
            return Response({"error": True, "message": "tag_id required"}, status=400)

        success = remove_tag_from_log(log_id, tag_id)
        if not success:
            return Response({"error": True, "message": "Cannot remove tag"}, status=400)
        return Response({"message": "Tag removed"})
