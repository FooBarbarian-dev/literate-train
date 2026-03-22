"""Tests for the api_keys module."""
import pytest

from api_keys.models import ApiKey


@pytest.mark.django_db
class TestApiKeyModel:
    def test_create_api_key(self, db):
        key = ApiKey.objects.create(
            name="Test Key",
            key_id="test-key-id-001",
            key_hash="fakehash123",
            created_by="admin",
        )
        assert key.is_active is True
        assert key.permissions == ["logs:write"]
        assert str(key) == "Test Key (test-key-id-001)"

    def test_revoke_key(self, db):
        key = ApiKey.objects.create(
            name="Revokable",
            key_id="revoke-id-001",
            key_hash="hash",
        )
        key.is_active = False
        key.save()
        key.refresh_from_db()
        assert key.is_active is False
