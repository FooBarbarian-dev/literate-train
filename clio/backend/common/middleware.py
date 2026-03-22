import json
import re

from django.http import JsonResponse


class SecurityHeadersMiddleware:
    """Adds security headers to all responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class CustomCsrfMiddleware:
    """Custom CSRF validation that skips checks for JWT-authenticated API
    requests and validates a CSRF token cookie/header pair for all others."""

    SAFE_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in self.SAFE_METHODS:
            return self.get_response(request)

        # Skip CSRF for requests authenticated via JWT (auth_token cookie)
        if request.COOKIES.get("auth_token"):
            return self.get_response(request)

        # For non-JWT requests, validate _csrf cookie against X-CSRF-Token header
        csrf_cookie = request.COOKIES.get("_csrf")
        csrf_header = request.META.get("HTTP_X_CSRF_TOKEN")

        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return JsonResponse(
                {"error": "CSRF validation failed."},
                status=403,
            )

        return self.get_response(request)


def _strip_html_tags(value):
    """Strip HTML tags from a string value."""
    return re.sub(r"<[^>]+>", "", value)


def _sanitize(data):
    """Recursively sanitize strings within dicts and lists."""
    if isinstance(data, dict):
        return {key: _sanitize(value) for key, value in data.items()}
    if isinstance(data, list):
        return [_sanitize(item) for item in data]
    if isinstance(data, str):
        return _strip_html_tags(data)
    return data


class InputSanitizationMiddleware:
    """Sanitizes request data by stripping HTML tags from string values
    in POST, PUT, and PATCH requests with application/json content type."""

    METHODS_TO_SANITIZE = ("POST", "PUT", "PATCH")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method in self.METHODS_TO_SANITIZE
            and request.content_type == "application/json"
            and hasattr(request, "data")
        ):
            request.data = _sanitize(request.data)

        return self.get_response(request)
