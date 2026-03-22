from dataclasses import dataclass
from typing import Optional

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from accounts.jwt_utils import verify_token, should_refresh_token, refresh_token


@dataclass
class JWTUser:
    """Lightweight user object. Not a Django model - identity lives in Redis."""
    username: str
    role: str
    admin_proof: str
    jti: str
    is_authenticated: bool = True
    is_active: bool = True

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def pk(self) -> str:
        return self.username

    @property
    def id(self) -> str:
        return self.username


class JWTCookieAuthentication(BaseAuthentication):
    """
    Extracts JWT from auth_token cookie or Authorization header.
    Performs full 7-step verification per spec Section 3.1.
    """

    def authenticate(self, request):
        token = self._extract_token(request)
        if not token:
            return None

        user_data = verify_token(token)
        user = JWTUser(**user_data)

        # Store decoded payload for refresh check
        request._jwt_token = token
        request._jwt_user = user

        return (user, token)

    def _extract_token(self, request) -> Optional[str]:
        # Try cookies first
        token = request.COOKIES.get("auth_token") or request.COOKIES.get("token")
        if token:
            return token

        # Try Authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        return None

    def authenticate_header(self, request):
        return "Bearer"
