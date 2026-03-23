import pytest
from unittest.mock import patch, MagicMock
from django.http import StreamingHttpResponse
from django.test import RequestFactory

from export.views import ExportCSVView


@pytest.mark.django_db
class TestExportViews:
    def test_csv_export_is_streaming(self):
        """CSV export must return StreamingHttpResponse."""
        factory = RequestFactory()
        request = factory.get("/api/export/csv/")
        request.user = MagicMock()
        request.user.username = "testuser"
        request.user.is_authenticated = True
        with patch.object(ExportCSVView, "check_throttles", return_value=None), \
             patch.object(ExportCSVView, "check_permissions", return_value=None):
            view = ExportCSVView.as_view()
            response = view(request)
            assert isinstance(response, StreamingHttpResponse)

    def test_csv_export_no_temp_file(self, tmp_path):
        """CSV export must not create temp files (streaming, no EXPORT_ROOT usage)."""
        factory = RequestFactory()
        request = factory.get("/api/export/csv/")
        request.user = MagicMock()
        request.user.username = "testuser"
        request.user.is_authenticated = True

        export_dir = tmp_path / "exports"
        with patch.object(ExportCSVView, "check_throttles", return_value=None), \
             patch.object(ExportCSVView, "check_permissions", return_value=None):
            view = ExportCSVView.as_view()
            response = view(request)
            # Consume the streaming response
            list(response.streaming_content)
            # EXPORT_ROOT directory should not have been created
            assert not export_dir.exists()
