"""Tests for the logs module: models, services, and API endpoints."""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from django.test import TestCase

from logs.models import Log
from logs.services import check_log_lock, toggle_lock


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestLogModel:
    def test_create_log(self, create_log):
        log = create_log()
        assert log.pk is not None
        assert log.hostname == "target-host"
        assert str(log).startswith("Log ")

    def test_ordering(self, create_log):
        log1 = create_log(timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc))
        log2 = create_log(timestamp=datetime(2025, 1, 2, tzinfo=timezone.utc))
        logs = list(Log.objects.all())
        assert logs[0].pk == log2.pk  # newer first

    def test_default_fields(self, create_log):
        log = create_log()
        assert log.locked is False
        assert log.locked_by == ""
        assert log.secrets == ""


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestCheckLogLock:
    def test_unlocked_log_always_editable(self, create_log):
        log = create_log(locked=False)
        assert check_log_lock(log, "anyone", False)

    def test_locked_by_same_user(self, create_log):
        log = create_log(locked=True, locked_by="operator1")
        assert check_log_lock(log, "operator1", False)

    def test_locked_by_different_user(self, create_log):
        log = create_log(locked=True, locked_by="operator1")
        assert not check_log_lock(log, "operator2", False)

    def test_admin_can_edit_locked(self, create_log):
        log = create_log(locked=True, locked_by="operator1")
        assert check_log_lock(log, "admin", True)


class TestToggleLock:
    def test_lock_unlocked_log(self, create_log):
        log = create_log(locked=False)
        result = toggle_lock(log, "operator1", False)
        assert result.locked is True
        assert result.locked_by == "operator1"

    def test_unlock_own_log(self, create_log):
        log = create_log(locked=True, locked_by="operator1")
        result = toggle_lock(log, "operator1", False)
        assert result.locked is False

    def test_cannot_unlock_others_log(self, create_log):
        log = create_log(locked=True, locked_by="operator1")
        with pytest.raises(PermissionError):
            toggle_lock(log, "operator2", False)

    def test_admin_can_unlock_any(self, create_log):
        log = create_log(locked=True, locked_by="operator1")
        result = toggle_lock(log, "admin", True)
        assert result.locked is False


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogListAPI:
    def test_unauthenticated_rejected(self, api_client):
        response = api_client.get("/api/logs/")
        assert response.status_code in (401, 403)

    def test_authenticated_returns_logs(self, authenticated_client, create_log):
        create_log()
        # Without active operation, non-admin gets empty queryset
        response = authenticated_client.get("/api/logs/")
        assert response.status_code == 200

    def test_admin_sees_all_without_active_op(self, admin_client, create_log):
        create_log()
        create_log(hostname="second-host")
        response = admin_client.get("/api/logs/")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", data)
        assert len(results) >= 2


@pytest.mark.django_db
class TestLogCreateAPI:
    def test_create_log(self, admin_client):
        payload = {
            "timestamp": "2025-01-15T10:30:00Z",
            "hostname": "new-target",
            "internal_ip": "10.0.0.100",
            "command": "id",
            "status": "success",
        }
        response = admin_client.post("/api/logs/", payload, format="json")
        assert response.status_code == 201
        assert Log.objects.filter(hostname="new-target").exists()


@pytest.mark.django_db
class TestLogDeleteAPI:
    def test_non_admin_cannot_delete(self, authenticated_client, create_log):
        log = create_log()
        response = authenticated_client.delete(f"/api/logs/{log.pk}/")
        assert response.status_code == 403

    def test_admin_can_delete(self, admin_client, create_log):
        log = create_log()
        response = admin_client.delete(f"/api/logs/{log.pk}/")
        assert response.status_code == 204
        assert not Log.objects.filter(pk=log.pk).exists()


@pytest.mark.django_db
class TestLogBulkDeleteAPI:
    def test_bulk_delete_admin(self, admin_client, create_log):
        l1 = create_log(hostname="a")
        l2 = create_log(hostname="b")
        response = admin_client.post(
            "/api/logs/bulk-delete/",
            {"ids": [l1.pk, l2.pk]},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["deleted"] == 2

    def test_bulk_delete_non_admin_rejected(self, authenticated_client, create_log):
        l1 = create_log()
        response = authenticated_client.post(
            "/api/logs/bulk-delete/",
            {"ids": [l1.pk]},
            format="json",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestLogToggleLockAPI:
    def test_toggle_lock(self, admin_client, create_log):
        log = create_log()
        response = admin_client.post(f"/api/logs/{log.pk}/toggle-lock/")
        assert response.status_code == 200
        log.refresh_from_db()
        assert log.locked is True


@pytest.mark.django_db
class TestLogFilterAPI:
    def test_filter_by_hostname(self, admin_client, create_log):
        create_log(hostname="webserver")
        create_log(hostname="dbserver")
        response = admin_client.get("/api/logs/", {"hostname": "web"})
        assert response.status_code == 200
        results = response.json().get("results", response.json())
        hostnames = [r["hostname"] for r in results]
        assert all("web" in h.lower() for h in hostnames)
