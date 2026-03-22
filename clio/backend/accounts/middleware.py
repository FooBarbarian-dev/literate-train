import json
import secrets

from django.http import JsonResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin

from accounts.sanitizers import sanitize_field


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Adds security headers per spec Section 13.3."""

    def process_response(self, request, response):
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
            "frame-src 'none'; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; upgrade-insecure-requests; block-all-mixed-content"
        )
        response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response["X-Frame-Options"] = "DENY"
        response["X-Content-Type-Options"] = "nosniff"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "no-referrer, strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "document-domain=(), sync-xhr=()"
        response["Cross-Origin-Embedder-Policy"] = "require-corp"
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Cross-Origin-Resource-Policy"] = "same-site"
        response["Cache-Control"] = "no-store, max-age=0"
        return response


class CustomCsrfMiddleware(CsrfViewMiddleware):
    """Custom CSRF with spec-specific bypass rules."""

    def _should_bypass(self, request):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.path.startswith("/api/ingest/"):
            return True
        if request.META.get("HTTP_X_API_REQUEST") == "true":
            return True
        return False

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if self._should_bypass(request):
            return None

        csrf_cookie = request.COOKIES.get("_csrf")
        csrf_header = (
            request.META.get("HTTP_CSRF_TOKEN")
            or request.META.get("HTTP_X_CSRF_TOKEN")
        )

        if not csrf_cookie or not csrf_header:
            return JsonResponse(
                {"error": True, "message": "CSRF token missing"},
                status=403,
            )

        if not secrets.compare_digest(csrf_cookie, csrf_header):
            return JsonResponse(
                {"error": True, "message": "CSRF token mismatch"},
                status=403,
            )

        return None


class InputSanitizationMiddleware(MiddlewareMixin):
    """Sanitizes all input fields per spec Section 13.1."""

    FIELD_MAX_LENGTHS = {
        "internal_ip": 45,
        "external_ip": 45,
        "mac_address": 17,
        "hostname": 75,
        "domain": 75,
        "username": 75,
        "command": 254,
        "notes": 254,
        "filename": 254,
        "status": 75,
        "secrets": 254,
        "hash_algorithm": 50,
        "hash_value": 128,
        "pid": 20,
        "analyst": 100,
        "name": 100,
        "description": 1000,
        "password": 128,
    }

    def process_request(self, request):
        if request.content_type and "json" in request.content_type:
            try:
                if hasattr(request, "body") and request.body:
                    data = json.loads(request.body)
                    if isinstance(data, dict):
                        sanitized = self._sanitize_dict(data)
                        request._body = json.dumps(sanitized).encode()
                    elif isinstance(data, list):
                        sanitized = [
                            self._sanitize_dict(item) if isinstance(item, dict) else item
                            for item in data
                        ]
                        request._body = json.dumps(sanitized).encode()
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    def _sanitize_dict(self, data: dict) -> dict:
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                max_len = self.FIELD_MAX_LENGTHS.get(key)
                if max_len and len(value) > max_len:
                    continue  # Skip oversized fields silently or could raise 400
                result[key] = sanitize_field(key, value)
            elif isinstance(value, dict):
                result[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict)
                    else sanitize_field(key, item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
