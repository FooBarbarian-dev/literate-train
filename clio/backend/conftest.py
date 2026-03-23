import pytest
from datetime import datetime, timezone
from rest_framework.test import APIClient

from logs.models import Log
from tags.models import Tag, LogTag
from operations.models import Operation, UserOperation
from api_keys.models import ApiKey


@pytest.fixture
def api_client():
    """DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def jwt_cookie(api_client):
    """Set a mock JWT cookie on the api_client that bypasses authentication."""
    api_client.cookies["auth_token"] = "mock-jwt-token"
    return api_client


@pytest.fixture
def make_tag(db):
    """Factory fixture for Tag."""
    def _make_tag(**kwargs):
        defaults = {
            "name": "test-tag",
            "color": "#FF0000",
            "category": "test",
            "created_by": "testuser",
        }
        defaults.update(kwargs)
        return Tag.objects.create(**defaults)
    return _make_tag


@pytest.fixture
def make_operation(db, make_tag):
    """Factory fixture for Operation."""
    def _make_operation(**kwargs):
        defaults = {
            "name": "test-operation",
            "description": "Test operation",
            "created_by": "testuser",
        }
        defaults.update(kwargs)
        return Operation.objects.create(**defaults)
    return _make_operation


@pytest.fixture
def make_user_operation(db, make_operation):
    """Factory fixture for UserOperation."""
    def _make_user_operation(**kwargs):
        if "operation" not in kwargs and "operation_id" not in kwargs:
            kwargs["operation"] = make_operation()
        defaults = {
            "username": "testuser",
            "assigned_by": "admin",
        }
        defaults.update(kwargs)
        return UserOperation.objects.create(**defaults)
    return _make_user_operation


@pytest.fixture
def make_log(db):
    """Factory fixture for Log."""
    def _make_log(**kwargs):
        defaults = {
            "timestamp": datetime.now(timezone.utc),
            "hostname": "test-host",
            "username": "testuser",
            "command": "test command",
            "analyst": "analyst1",
        }
        defaults.update(kwargs)
        return Log.objects.create(**defaults)
    return _make_log


@pytest.fixture
def make_api_key(db):
    """Factory fixture for ApiKey."""
    def _make_api_key(**kwargs):
        defaults = {
            "name": "test-key",
            "key_id": "test-key-id",
            "key_hash": "testhash",
            "created_by": "testuser",
        }
        defaults.update(kwargs)
        return ApiKey.objects.create(**defaults)
    return _make_api_key
