import hashlib
import os
import uuid

from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from accounts.permissions import IsJWTAuthenticated
from evidence.models import EvidenceFile
from evidence.serializers import (
    EvidenceFileSerializer,
    EvidenceFileCreateSerializer,
    EvidenceFileUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List evidence files", tags=["evidence"]),
    create=extend_schema(summary="Create evidence metadata", tags=["evidence"]),
    retrieve=extend_schema(summary="Get an evidence file", tags=["evidence"]),
    update=extend_schema(summary="Update evidence metadata", tags=["evidence"]),
    partial_update=extend_schema(summary="Partially update evidence", tags=["evidence"]),
    destroy=extend_schema(summary="Delete an evidence file", tags=["evidence"]),
)
class EvidenceFileViewSet(viewsets.ModelViewSet):
    serializer_class = EvidenceFileSerializer
    permission_classes = [IsJWTAuthenticated]

    def get_queryset(self):
        qs = EvidenceFile.objects.all()
        log_id = self.request.query_params.get("log_id")
        if log_id:
            qs = qs.filter(log_id=log_id)
        return qs

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return EvidenceFileUpdateSerializer
        return EvidenceFileSerializer

    @extend_schema(
        request=EvidenceFileCreateSerializer,
        summary="Upload an evidence file",
        tags=["evidence"],
    )
    @action(detail=False, methods=["post"])
    def upload(self, request):
        serializer = EvidenceFileCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        log_id = serializer.validated_data["log_id"]
        description = serializer.validated_data.get("description", "")

        # Compute MD5 hash
        md5 = hashlib.md5()
        for chunk in uploaded_file.chunks():
            md5.update(chunk)
        md5_hash = md5.hexdigest()

        # Generate unique filename
        ext = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # Ensure evidence directory exists
        evidence_root = getattr(settings, "EVIDENCE_ROOT", "/app/data/evidence")
        os.makedirs(evidence_root, exist_ok=True)

        filepath = os.path.join(evidence_root, unique_filename)

        # Write file to disk
        uploaded_file.seek(0)
        with open(filepath, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        evidence = EvidenceFile.objects.create(
            log_id=log_id,
            filename=unique_filename,
            original_filename=uploaded_file.name,
            file_type=uploaded_file.content_type or "",
            file_size=uploaded_file.size,
            uploaded_by=request.user.username,
            description=description,
            md5_hash=md5_hash,
            filepath=filepath,
        )

        return Response(
            EvidenceFileSerializer(evidence).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="Download an evidence file", tags=["evidence"])
    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        evidence = self.get_object()

        if not os.path.exists(evidence.filepath):
            return Response(
                {"error": True, "message": "File not found on disk"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            open(evidence.filepath, "rb"),
            as_attachment=True,
            filename=evidence.original_filename,
        )
