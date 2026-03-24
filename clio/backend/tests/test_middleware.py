import json
import secrets
from unittest.mock import patch

import pytest
from django.test import RequestFactory
from rest_framework.test import APIClient

from common.middleware import InputSanitizationMiddleware, CustomCsrfMiddleware


@pytest.mark.django_db
class TestInputSanitizationMiddleware:
    def test_input_sanitization_runs(self):
        """POST with JSON body containing script tag gets sanitized."""
        factory = RequestFactory()
        body = json.dumps({"name": "<script>alert(1)</script>hello"})
        request = factory.post(
            "/api/test/",
            data=body,
            content_type="application/json",
        )
        called = {}

        def get_response(req):
            called["body"] = req.body
            from django.http import HttpResponse
            return HttpResponse("ok")

        middleware = InputSanitizationMiddleware(get_response)
        middleware(request)

        sanitized = json.loads(called["body"])
        assert "<script>" not in sanitized["name"]
        assert "hello" in sanitized["name"]


class TestCsrfTimingSafe:
    def test_csrf_timing_safe(self):
        """CustomCsrfMiddleware uses secrets.compare_digest."""
        import inspect
        source = inspect.getsource(CustomCsrfMiddleware)
        assert "secrets.compare_digest" in source


_MOCK_AUTH_RESULT = {
    "username": "analyst",
    "role": "user",
    "requiresPasswordChange": False,
}
_MOCK_TOKEN = "mock.jwt.token"
_MOCK_PAYLOAD = {"jti": "abc123", "username": "analyst", "role": "user"}


@pytest.mark.django_db
class TestLoginCsrfCookieLifecycle:
    """Login must always issue a fresh _csrf cookie and return the token value."""

    def _do_login(self, client):
        with (
            patch("accounts.views.authenticate_user", return_value=_MOCK_AUTH_RESULT),
            patch("accounts.views.issue_token", return_value=(_MOCK_TOKEN, _MOCK_PAYLOAD)),
        ):
            return client.post(
                "/api/accounts/login/",
                data=json.dumps({"username": "analyst", "password": "Pass1234!"}),
                content_type="application/json",
            )

    def test_login_sets_csrf_cookie(self):
        """A successful login must set the _csrf cookie."""
        client = APIClient()
        response = self._do_login(client)
        assert response.status_code == 200
        assert "_csrf" in response.cookies

    def test_login_returns_csrf_token_in_body(self):
        """The CSRF token value must be present in the response body."""
        client = APIClient()
        response = self._do_login(client)
        data = response.json()
        assert "csrfToken" in data
        assert len(data["csrfToken"]) == 64  # secrets.token_hex(32)

    def test_login_csrf_cookie_matches_body_token(self):
        """The _csrf cookie value must equal the csrfToken in the body."""
        client = APIClient()
        response = self._do_login(client)
        data = response.json()
        assert response.cookies["_csrf"].value == data["csrfToken"]

    def test_login_replaces_stale_csrf_cookie(self):
        """Re-login must issue a new token, not reuse the previous one."""
        client = APIClient()
        first = self._do_login(client)
        second = self._do_login(client)
        assert first.cookies["_csrf"].value != second.cookies["_csrf"].value


@pytest.mark.django_db
class TestLogoutCookieCleanup:
    """Logout must delete all three auth/CSRF cookies with the correct SameSite."""

    def test_logout_deletes_csrf_cookie(self):
        """POST /logout/ must expire the _csrf cookie."""
        client = APIClient()
        # Simulate an existing session so the middleware's JWT bypass fires.
        client.cookies["auth_token"] = _MOCK_TOKEN
        client.cookies["_csrf"] = "old-token"
        response = client.post("/api/accounts/logout/")
        assert response.status_code == 200
        assert response.cookies["_csrf"]["max-age"] == 0

    def test_logout_deletes_auth_token_cookie(self):
        """POST /logout/ must expire the auth_token cookie."""
        client = APIClient()
        client.cookies["auth_token"] = _MOCK_TOKEN
        response = client.post("/api/accounts/logout/")
        assert response.cookies["auth_token"]["max-age"] == 0

    def test_logout_samesite_matches_debug_setting(self, settings):
        """delete_cookie samesite must match the original cookie's setting."""
        settings.DEBUG = True
        client = APIClient()
        client.cookies["auth_token"] = _MOCK_TOKEN
        response = client.post("/api/accounts/logout/")
        assert response.cookies["auth_token"]["samesite"].lower() == "lax"
        assert response.cookies["_csrf"]["samesite"].lower() == "lax"


@pytest.mark.django_db
class TestVerifyCsrfCookieCleanup:
    """A failed verify must clear the _csrf cookie along with auth cookies."""

    def test_verify_deletes_csrf_on_unauthenticated(self):
        """GET /verify/ with no valid JWT must expire the _csrf cookie."""
        client = APIClient()
        # No auth_token — verify will return 401 and clear cookies.
        client.cookies["_csrf"] = "stale-csrf-token"
        response = client.get("/api/accounts/verify/")
        assert response.status_code == 401
        assert response.cookies["_csrf"]["max-age"] == 0


@pytest.mark.django_db
class TestCsrfDoubleSubmitValidation:
    """The CSRF double-submit check must block requests missing the header."""

    def test_post_without_auth_token_and_without_csrf_header_is_rejected(self):
        """A non-exempt POST with no JWT and no X-CSRF-Token must get 403."""
        factory = RequestFactory()
        # Use an endpoint that is not in CSRF_EXEMPT_PATHS and does not use JWT.
        request = factory.post(
            "/api/some/protected/",
            data="{}",
            content_type="application/json",
        )
        request.COOKIES["_csrf"] = "some-token"
        # X-CSRF-Token header intentionally omitted.

        from django.http import HttpResponse
        middleware = CustomCsrfMiddleware(lambda r: HttpResponse("ok"))
        response = middleware(request)
        assert response.status_code == 403

    def test_post_with_matching_csrf_header_passes(self):
        """A non-exempt POST with matching cookie+header pair must pass."""
        token = secrets.token_hex(32)
        factory = RequestFactory()
        request = factory.post(
            "/api/some/protected/",
            data="{}",
            content_type="application/json",
            HTTP_X_CSRF_TOKEN=token,
        )
        request.COOKIES["_csrf"] = token

        from django.http import HttpResponse
        middleware = CustomCsrfMiddleware(lambda r: HttpResponse("ok"))
        response = middleware(request)
        assert response.status_code == 200
