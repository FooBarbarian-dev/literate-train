"""
Tests for tag creation, log-tag add/remove, and log filtering by tag/status.
"""
import pytest

from accounts.authentication import JWTUser
from tags.models import Tag, LogTag


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def regular_user():
    return JWTUser(username="testuser", role="user", admin_proof="", jti="test-jti")


@pytest.fixture
def authed_client(api_client, regular_user):
    """API client authenticated as a regular (non-admin) user.

    Sets both force_authenticate (so DRF permissions see a real user) and
    the auth_token cookie (so CustomCsrfMiddleware skips CSRF for mutating
    requests without needing a real JWT).
    """
    api_client.force_authenticate(user=regular_user)
    api_client.cookies["auth_token"] = "mock-jwt-for-csrf-skip"
    return api_client


# ---------------------------------------------------------------------------
# Tag creation — any authenticated user (not admin-only)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTagCreation:
    URL = "/api/tags/tags/"

    def test_any_user_can_create_tag(self, authed_client):
        """Non-admin authenticated users must be able to POST /tags/tags/."""
        resp = authed_client.post(
            self.URL,
            {"name": "new-tag", "color": "#ff0000"},
            format="json",
        )
        assert resp.status_code == 201, resp.data
        assert Tag.objects.filter(name="new-tag").exists()

    def test_create_tag_with_description(self, authed_client):
        """Description field is stored and returned."""
        resp = authed_client.post(
            self.URL,
            {"name": "described-tag", "color": "#00ff00", "description": "A useful tag"},
            format="json",
        )
        assert resp.status_code == 201, resp.data
        tag = Tag.objects.get(name="described-tag")
        assert tag.description == "A useful tag"
        assert resp.data["description"] == "A useful tag"

    def test_create_tag_normalises_name_to_lowercase(self, authed_client):
        """Tag names are normalised to lowercase on creation."""
        resp = authed_client.post(
            self.URL,
            {"name": "MixedCase", "color": "#0000ff"},
            format="json",
        )
        assert resp.status_code == 201, resp.data
        assert Tag.objects.filter(name="mixedcase").exists()

    def test_unauthenticated_cannot_create_tag(self, api_client):
        """Requests without authentication must be rejected."""
        resp = api_client.post(
            self.URL,
            {"name": "sneaky-tag", "color": "#ffffff"},
            format="json",
        )
        assert resp.status_code in (401, 403)

    def test_invalid_color_rejected(self, authed_client):
        """Tags with a non-hex color are rejected by the serializer."""
        resp = authed_client.post(
            self.URL,
            {"name": "bad-color", "color": "not-a-color"},
            format="json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Log-tag add / remove
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogTagEndpoints:
    URL = "/api/tags/tags/log-tag/"

    def test_add_tag_to_log(self, authed_client, make_log, make_tag):
        """POST /api/tags/tags/log-tag/ creates a LogTag association."""
        log = make_log()
        tag = make_tag()
        resp = authed_client.post(
            self.URL,
            {"log_id": log.id, "tag_id": tag.id},
            format="json",
        )
        assert resp.status_code == 201, resp.data
        assert LogTag.objects.filter(log=log, tag=tag).exists()

    def test_remove_tag_from_log(self, authed_client, make_log, make_tag):
        """DELETE /api/tags/tags/log-tag/ removes an existing LogTag."""
        log = make_log()
        tag = make_tag()
        LogTag.objects.create(log=log, tag=tag, tagged_by="testuser")
        resp = authed_client.delete(
            self.URL,
            {"log_id": log.id, "tag_id": tag.id},
            format="json",
        )
        assert resp.status_code == 200, resp.data
        assert not LogTag.objects.filter(log=log, tag=tag).exists()

    def test_add_tag_missing_log_id_returns_400(self, authed_client, make_tag):
        tag = make_tag()
        resp = authed_client.post(self.URL, {"tag_id": tag.id}, format="json")
        assert resp.status_code == 400

    def test_add_tag_missing_tag_id_returns_400(self, authed_client, make_log):
        log = make_log()
        resp = authed_client.post(self.URL, {"log_id": log.id}, format="json")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Log filtering — status, tag, and internal_ip
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogFilters:
    URL = "/api/logs/logs/"

    def test_filter_by_status(self, authed_client, make_log):
        """?status=success only returns logs with that status."""
        make_log(hostname="success-host", status="success")
        make_log(hostname="failure-host", status="failure")

        resp = authed_client.get(self.URL, {"status": "success"})
        assert resp.status_code == 200, resp.data
        results = resp.data if isinstance(resp.data, list) else resp.data.get("results", [])
        assert all(r["status"] == "success" for r in results)
        hostnames = [r["hostname"] for r in results]
        assert "success-host" in hostnames
        assert "failure-host" not in hostnames

    def test_filter_by_tag_name(self, authed_client, make_log, make_tag):
        """?tag=<name> only returns logs associated with that tag."""
        tagged_log = make_log(hostname="tagged-host")
        make_log(hostname="untagged-host")
        tag = make_tag(name="filter-tag")
        LogTag.objects.create(log=tagged_log, tag=tag, tagged_by="testuser")

        resp = authed_client.get(self.URL, {"tag": "filter-tag"})
        assert resp.status_code == 200, resp.data
        results = resp.data if isinstance(resp.data, list) else resp.data.get("results", [])
        hostnames = [r["hostname"] for r in results]
        assert "tagged-host" in hostnames
        assert "untagged-host" not in hostnames

    def test_filter_by_internal_ip(self, authed_client, make_log):
        """?internal_ip= filters by IP (partial match)."""
        make_log(hostname="host-a", internal_ip="10.0.0.1")
        make_log(hostname="host-b", internal_ip="192.168.1.1")

        resp = authed_client.get(self.URL, {"internal_ip": "10.0.0"})
        assert resp.status_code == 200, resp.data
        results = resp.data if isinstance(resp.data, list) else resp.data.get("results", [])
        hostnames = [r["hostname"] for r in results]
        assert "host-a" in hostnames
        assert "host-b" not in hostnames
