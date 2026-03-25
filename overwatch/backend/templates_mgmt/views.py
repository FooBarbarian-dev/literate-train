from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from accounts.permissions import IsJWTAuthenticated
from templates_mgmt.models import LogTemplate
from templates_mgmt.serializers import LogTemplateSerializer, LogTemplateCreateSerializer


@extend_schema_view(
    list=extend_schema(summary="List log templates", tags=["templates"]),
    create=extend_schema(summary="Create a log template", tags=["templates"]),
    retrieve=extend_schema(summary="Get a log template", tags=["templates"]),
    update=extend_schema(summary="Update a log template", tags=["templates"]),
    partial_update=extend_schema(summary="Partially update a log template", tags=["templates"]),
    destroy=extend_schema(summary="Delete a log template", tags=["templates"]),
)
class LogTemplateViewSet(viewsets.ModelViewSet):
    queryset = LogTemplate.objects.all().order_by("-updated_at")
    serializer_class = LogTemplateSerializer
    permission_classes = [IsJWTAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return LogTemplateCreateSerializer
        return LogTemplateSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    @extend_schema(summary="Apply a template (get template data)", tags=["templates"])
    @action(detail=True, methods=["get"])
    def apply(self, request, pk=None):
        template = self.get_object()
        return Response({
            "template_id": template.id,
            "name": template.name,
            "template_data": template.template_data,
        })
