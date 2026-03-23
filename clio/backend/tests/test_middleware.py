import json
import secrets
from unittest.mock import patch

import pytest
from django.test import RequestFactory

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
