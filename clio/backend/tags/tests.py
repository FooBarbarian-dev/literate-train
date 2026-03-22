"""Tests for the tags module: models, services, and API endpoints."""
import pytest

from tags.models import Tag, LogTag
from tags.services import is_operation_tag, add_tag_to_log, remove_tag_from_log


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestTagModel:
    def test_create_tag(self, create_tag):
        tag = create_tag(name="Persistence")
        assert tag.name == "persistence"  # auto-lowercased

    def test_unique_name(self, create_tag):
        create_tag(name="unique-tag")
        with pytest.raises(Exception):
            create_tag(name="unique-tag")

    def test_default_color(self, db):
        tag = Tag.objects.create(name="no-color")
        assert tag.color == "#6B7280"


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestIsOperationTag:
    def test_operation_tag(self, create_tag):
        tag = create_tag(name="op:crimson-hawk", category="operation")
        assert is_operation_tag(tag)

    def test_regular_tag(self, create_tag):
        tag = create_tag(name="persistence")
        assert not is_operation_tag(tag)


class TestAddRemoveTag:
    def test_add_tag_to_log(self, create_log, create_tag):
        log = create_log()
        tag = create_tag(name="test-add")
        add_tag_to_log(log.pk, tag.pk, "operator1")
        assert LogTag.objects.filter(log=log, tag=tag).exists()

    def test_add_duplicate_tag(self, create_log, create_tag):
        log = create_log()
        tag = create_tag(name="test-dup")
        add_tag_to_log(log.pk, tag.pk, "operator1")
        # Second add should not raise
        add_tag_to_log(log.pk, tag.pk, "operator1")
        assert LogTag.objects.filter(log=log, tag=tag).count() == 1

    def test_remove_tag_from_log(self, create_log, create_tag):
        log = create_log()
        tag = create_tag(name="test-remove")
        add_tag_to_log(log.pk, tag.pk, "operator1")
        remove_tag_from_log(log.pk, tag.pk)
        assert not LogTag.objects.filter(log=log, tag=tag).exists()


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTagListAPI:
    def test_authenticated_can_list(self, authenticated_client, create_tag):
        create_tag(name="api-tag-1")
        create_tag(name="api-tag-2")
        response = authenticated_client.get("/api/tags/")
        assert response.status_code == 200

    def test_unauthenticated_rejected(self, api_client):
        response = api_client.get("/api/tags/")
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestTagCreateAPI:
    def test_admin_can_create(self, admin_client):
        response = admin_client.post(
            "/api/tags/",
            {"name": "new-api-tag", "color": "#FF0000"},
            format="json",
        )
        assert response.status_code == 201
        assert Tag.objects.filter(name="new-api-tag").exists()

    def test_non_admin_cannot_create(self, authenticated_client):
        response = authenticated_client.post(
            "/api/tags/",
            {"name": "blocked-tag", "color": "#FF0000"},
            format="json",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestTagDeleteAPI:
    def test_cannot_delete_operation_tag(self, admin_client, create_tag):
        tag = create_tag(name="op:test-op", category="operation")
        response = admin_client.delete(f"/api/tags/{tag.pk}/")
        assert response.status_code in (400, 403)

    def test_can_delete_regular_tag(self, admin_client, create_tag):
        tag = create_tag(name="deletable")
        response = admin_client.delete(f"/api/tags/{tag.pk}/")
        assert response.status_code == 204
