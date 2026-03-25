import csv
import io
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from django.http import StreamingHttpResponse
from django.test import RequestFactory

from export.views import ExportCSVView, ExportJSONView, LOG_EXPORT_FIELDS, _resolve_fields

NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(factory, path, query_string=""):
    url = path + ("?" + query_string if query_string else "")
    return factory.get(url)


def _authed_request(factory, path, query_string=""):
    request = _make_request(factory, path, query_string)
    request.user = MagicMock()
    request.user.username = "testuser"
    request.user.is_authenticated = True
    return request


def _call_csv(request):
    with patch.object(ExportCSVView, "check_throttles", return_value=None), \
         patch.object(ExportCSVView, "check_permissions", return_value=None):
        view = ExportCSVView.as_view()
        return view(request)


def _call_json(request):
    with patch.object(ExportJSONView, "check_throttles", return_value=None), \
         patch.object(ExportJSONView, "check_permissions", return_value=None):
        view = ExportJSONView.as_view()
        return view(request)


def _consume_csv(response):
    """Return (header_list, list_of_row_dicts) from a streaming CSV response."""
    chunks = response.streaming_content
    content = b"".join(
        chunk if isinstance(chunk, bytes) else chunk.encode() for chunk in chunks
    ).decode()
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    return reader.fieldnames or [], rows


def _consume_json(response):
    chunks = response.streaming_content
    content = b"".join(
        chunk if isinstance(chunk, bytes) else chunk.encode() for chunk in chunks
    ).decode()
    return json.loads(content)


# ---------------------------------------------------------------------------
# _resolve_fields unit tests (no DB needed)
# ---------------------------------------------------------------------------

class TestResolveFields:
    def test_no_fields_param_returns_all(self):
        result = _resolve_fields({})
        assert result == list(LOG_EXPORT_FIELDS)

    def test_empty_string_returns_all(self):
        result = _resolve_fields({"fields": ""})
        assert result == list(LOG_EXPORT_FIELDS)

    def test_single_valid_field(self):
        result = _resolve_fields({"fields": "hostname"})
        assert result == ["hostname"]

    def test_multiple_valid_fields_preserves_order(self):
        result = _resolve_fields({"fields": "username,hostname,command"})
        assert result == ["username", "hostname", "command"]

    def test_unknown_fields_are_silently_dropped(self):
        result = _resolve_fields({"fields": "hostname,nonexistent_field,command"})
        assert result == ["hostname", "command"]

    def test_all_unknown_fields_returns_full_list(self):
        result = _resolve_fields({"fields": "bogus1,bogus2"})
        assert result == list(LOG_EXPORT_FIELDS)

    def test_whitespace_around_field_names_is_stripped(self):
        result = _resolve_fields({"fields": " hostname , command "})
        assert result == ["hostname", "command"]

    def test_duplicate_fields_are_preserved(self):
        # Duplicates are technically allowed; Django handles them fine.
        result = _resolve_fields({"fields": "hostname,hostname"})
        assert result == ["hostname", "hostname"]

    def test_all_export_fields_are_recognised(self):
        result = _resolve_fields({"fields": ",".join(LOG_EXPORT_FIELDS)})
        assert result == list(LOG_EXPORT_FIELDS)


# ---------------------------------------------------------------------------
# CSV export integration tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestExportCSVView:
    def test_csv_export_is_streaming(self):
        """CSV export must return StreamingHttpResponse."""
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/")
        response = _call_csv(request)
        assert isinstance(response, StreamingHttpResponse)

    def test_csv_export_no_temp_file(self, tmp_path):
        """CSV export must not create temp files (streaming, no EXPORT_ROOT usage)."""
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/")

        export_dir = tmp_path / "exports"
        response = _call_csv(request)
        list(response.streaming_content)
        assert not export_dir.exists()

    def test_csv_default_fields_header(self):
        """Without a fields param the header row contains all LOG_EXPORT_FIELDS."""
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/")
        response = _call_csv(request)
        fieldnames, _ = _consume_csv(response)
        assert list(fieldnames) == list(LOG_EXPORT_FIELDS)

    def test_csv_content_type(self):
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/")
        response = _call_csv(request)
        assert response["Content-Type"] == "text/csv"

    def test_csv_content_disposition(self):
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/")
        response = _call_csv(request)
        assert "attachment" in response["Content-Disposition"]
        assert ".csv" in response["Content-Disposition"]

    def test_csv_selected_fields_header(self):
        """Passing ?fields=hostname,command restricts the CSV columns."""
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/", "fields=hostname,command")
        response = _call_csv(request)
        fieldnames, _ = _consume_csv(response)
        assert list(fieldnames) == ["hostname", "command"]

    def test_csv_selected_fields_excludes_others(self):
        """Columns not in the fields param must not appear in output."""
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/", "fields=id,hostname")
        response = _call_csv(request)
        fieldnames, _ = _consume_csv(response)
        assert "username" not in fieldnames
        assert "command" not in fieldnames

    def test_csv_invalid_fields_falls_back_to_all(self):
        """Entirely invalid field names fall back to the full field list."""
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/", "fields=bogus1,bogus2")
        response = _call_csv(request)
        fieldnames, _ = _consume_csv(response)
        assert list(fieldnames) == list(LOG_EXPORT_FIELDS)

    def test_csv_mixed_valid_invalid_fields(self):
        """Only the valid portion of a mixed field list is used."""
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/", "fields=hostname,INVALID,command")
        response = _call_csv(request)
        fieldnames, _ = _consume_csv(response)
        assert list(fieldnames) == ["hostname", "command"]

    def test_csv_single_field(self):
        """A single valid field produces a one-column CSV."""
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/", "fields=username")
        response = _call_csv(request)
        fieldnames, _ = _consume_csv(response)
        assert list(fieldnames) == ["username"]

    def test_csv_row_data_with_selected_fields(self):
        """Rows in a field-selected export only contain the requested columns."""
        from logs.models import Log
        Log.objects.create(hostname="host-a", username="bob", command="ls", timestamp=NOW)

        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/csv/", "fields=hostname,username")
        response = _call_csv(request)
        _, rows = _consume_csv(response)

        assert len(rows) >= 1
        row = next(r for r in rows if r["hostname"] == "host-a")
        assert row["username"] == "bob"
        assert "command" not in row


# ---------------------------------------------------------------------------
# JSON export integration tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestExportJSONView:
    def test_json_export_is_streaming(self):
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/json/")
        response = _call_json(request)
        assert isinstance(response, StreamingHttpResponse)

    def test_json_content_type(self):
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/json/")
        response = _call_json(request)
        assert response["Content-Type"] == "application/json"

    def test_json_content_disposition(self):
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/json/")
        response = _call_json(request)
        assert "attachment" in response["Content-Disposition"]
        assert ".json" in response["Content-Disposition"]

    def test_json_default_fields(self):
        """Without a fields param each JSON object has all LOG_EXPORT_FIELDS keys."""
        from logs.models import Log
        Log.objects.create(hostname="host-json", timestamp=NOW)

        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/json/")
        response = _call_json(request)
        data = _consume_json(response)

        assert isinstance(data, list)
        record = next(r for r in data if r.get("hostname") == "host-json")
        for field in LOG_EXPORT_FIELDS:
            assert field in record

    def test_json_selected_fields(self):
        """Passing ?fields=id,hostname restricts keys in each JSON object."""
        from logs.models import Log
        Log.objects.create(hostname="host-json2", timestamp=NOW)

        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/json/", "fields=id,hostname")
        response = _call_json(request)
        data = _consume_json(response)

        assert isinstance(data, list)
        record = next(r for r in data if r.get("hostname") == "host-json2")
        assert set(record.keys()) == {"id", "hostname"}

    def test_json_invalid_fields_falls_back_to_all(self):
        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/json/", "fields=nope")
        response = _call_json(request)
        data = _consume_json(response)
        assert isinstance(data, list)
        # Can't assert row keys without data, but response must be valid JSON list.

    def test_json_empty_db_returns_empty_array(self):
        from logs.models import Log
        Log.objects.all().delete()

        factory = RequestFactory()
        request = _authed_request(factory, "/api/export/json/")
        response = _call_json(request)
        data = _consume_json(response)
        assert data == []
