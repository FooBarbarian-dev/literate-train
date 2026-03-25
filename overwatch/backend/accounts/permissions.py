from rest_framework.permissions import BasePermission

from accounts.jwt_utils import verify_admin_proof


class IsJWTAuthenticated(BasePermission):
    """Requires a valid JWT token."""

    def has_permission(self, request, view) -> bool:
        return (
            request.user is not None
            and hasattr(request.user, "is_authenticated")
            and request.user.is_authenticated
        )


class IsAdmin(BasePermission):
    """Requires admin role with valid HMAC proof."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
            return False
        if not hasattr(user, "role") or user.role != "admin":
            return False
        if not hasattr(user, "admin_proof") or not user.admin_proof:
            return False
        return verify_admin_proof(user.username, user.admin_proof)
