import pytest
from django.conf import settings


class TestAuthConfig:
    def test_jwt_authentication_class_registered(self):
        """JWTCookieAuthentication must be in DEFAULT_AUTHENTICATION_CLASSES."""
        auth_classes = settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
        assert "accounts.authentication.JWTCookieAuthentication" in auth_classes
