"""
Root conftest for the Clio platform backend test suite.

Provides fixtures for:
- Test database configuration (SQLite in-memory)
- Mocked Redis (no real Redis required)
- DRF API clients (anonymous, authenticated, admin)
- Factory functions for creating test model instances
"""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient

from accounts.authentication import JWTUser


# ---------------------------------------------------------------------------
# Environment setup for tests
# ---------------------------------------------------------------------------

# AES-256-GCM requires a 32-byte (64 hex char) key
TEST_ENCRYPTION_KEY = "a" * 64

os.environ.setdefault("FIELD_ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)
os.environ.setdefault("REDIS_ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key")
os.environ.setdefault("ADMIN_SECRET", "test-admin-secret")
os.environ.setdefault("SERVER_INSTANCE_ID", "test-instance")


# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _use_test_settings(settings):
    """Override database to use SQLite in-memory for fast tests."""
    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    # Disable throttling in tests
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }


# ---------------------------------------------------------------------------
# Mock Redis
# ---------------------------------------------------------------------------

class FakeRedis:
    """In-memory fake that implements the EncryptedRedis interface.

    Values are stored as plain strings (no encryption) since we only need
    to exercise the application logic, not the actual AES-GCM layer.
    """

    def __init__(self):
        self._store = {}
        self._sets = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, ex=None):
        self._store[key] = value

    def delete(self, key):
        self._store.pop(key, None)
        self._sets.pop(key, None)

    def exists(self, key):
        return key in self._store or key in self._sets

    def keys(self, pattern="*"):
        import fnmatch
        all_keys = list(self._store.keys()) + list(self._sets.keys())
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def sadd(self, key, *values):
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].update(values)

    def smembers(self, key):
        return self._sets.get(key, set())

    def srem(self, key, *values):
        if key in self._sets:
            self._sets[key] -= set(values)

    def expire(self, key, seconds):
        pass

    def ttl(self, key):
        return -1

    def scan_iter(self, match="*"):
        return self.keys(match)


@pytest.fixture()
def fake_redis():
    """Provide a FakeRedis instance and patch common.redis_client."""
    fake = FakeRedis()
    with patch("common.redis_client.get_encrypted_redis", return_value=fake):
        # Also reset the module-level singleton so it picks up the fake
        import common.redis_client as rc_module
        old = rc_module._encrypted_redis
        rc_module._encrypted_redis = fake
        yield fake
        rc_module._encrypted_redis = old


@pytest.fixture(autouse=True)
def mock_redis():
    """Auto-mock Redis for every test so nothing hits a real Redis server."""
    fake = FakeRedis()
    with patch("common.redis_client.get_encrypted_redis", return_value=fake):
        import common.redis_client as rc_module
        old = rc_module._encrypted_redis
        rc_module._encrypted_redis = fake
        yield fake
        rc_module._encrypted_redis = old


# ---------------------------------------------------------------------------
# JWT user helpers
# ---------------------------------------------------------------------------

def make_jwt_user(username="testuser", role="operator", admin_proof="", jti="test-jti-001"):
    """Create a JWTUser dataclass instance for testing."""
    if role == "admin" and not admin_proof:
        import hashlib
        import hmac as _hmac
        secret = os.environ.get("ADMIN_SECRET", "test-admin-secret")
        admin_proof = _hmac.new(
            secret.encode(), username.encode(), hashlib.sha256
        ).hexdigest()
    return JWTUser(
        username=username,
        role=role,
        admin_proof=admin_proof,
        jti=jti,
    )


# ---------------------------------------------------------------------------
# API clients
# ---------------------------------------------------------------------------

@pytest.fixture()
def api_client():
    """Unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture()
def authenticated_client():
    """APIClient authenticated as a regular operator user.

    Patches JWTCookieAuthentication so that every request is treated as
    coming from the test user without needing a real JWT token.
    """
    client = APIClient()
    user = make_jwt_user(username="testoperator", role="operator")

    with patch(
        "accounts.authentication.JWTCookieAuthentication.authenticate",
        return_value=(user, "fake-token"),
    ):
        client.cookies["auth_token"] = "fake-token"
        yield client


@pytest.fixture()
def admin_client():
    """APIClient authenticated as an admin user.

    Patches JWTCookieAuthentication so that every request is treated as
    coming from the admin user.
    """
    client = APIClient()
    user = make_jwt_user(username="testadmin", role="admin")

    with patch(
        "accounts.authentication.JWTCookieAuthentication.authenticate",
        return_value=(user, "fake-admin-token"),
    ):
        client.cookies["auth_token"] = "fake-admin-token"
        yield client


# ---------------------------------------------------------------------------
# Model factory helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def create_log(db):
    """Factory fixture to create Log instances."""
    from logs.models import Log

    def _create_log(**kwargs):
        defaults = {
            "timestamp": datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "hostname": "target-host",
            "internal_ip": "10.0.0.50",
            "external_ip": "203.0.113.10",
            "command": "whoami",
            "analyst": "testoperator",
        }
        defaults.update(kwargs)
        return Log.objects.create(**defaults)

    return _create_log


@pytest.fixture()
def create_tag(db):
    """Factory fixture to create Tag instances."""
    from tags.models import Tag

    def _create_tag(**kwargs):
        defaults = {
            "name": "test-tag",
            "color": "#FF5733",
            "category": "custom",
        }
        defaults.update(kwargs)
        return Tag.objects.create(**defaults)

    return _create_tag


@pytest.fixture()
def create_operation(db):
    """Factory fixture to create Operation instances (without the auto-tag trigger)."""
    from operations.models import Operation

    def _create_operation(**kwargs):
        defaults = {
            "name": "Test Operation",
            "description": "A test operation",
            "created_by": "testadmin",
        }
        defaults.update(kwargs)
        return Operation.objects.create(**defaults)

    return _create_operation


@pytest.fixture()
def create_user_operation(db):
    """Factory fixture to create UserOperation instances."""
    from operations.models import UserOperation

    def _create_user_operation(username, operation, **kwargs):
        defaults = {
            "username": username,
            "operation_id": operation,
            "assigned_by": "testadmin",
        }
        defaults.update(kwargs)
        return UserOperation.objects.create(**defaults)

    return _create_user_operation
