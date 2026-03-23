import os
import secrets
import time

from django.conf import settings as django_settings
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from accounts.authentication import JWTUser
from accounts.backends import authenticate_user, change_password, has_custom_password
from accounts.jwt_utils import issue_token, revoke_token, verify_token
from accounts.permissions import IsJWTAuthenticated
from accounts.serializers import LoginSerializer, PasswordChangeSerializer
from accounts.throttles import AuthRateThrottle
from accounts.validators import validate_username, validate_password, validate_password_input


@extend_schema(
    request=LoginSerializer,
    responses={200: dict},
    summary="Login with username and password",
    tags=["auth"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    try:
        validate_username(username)
    except Exception:
        return Response(
            {"error": True, "message": "Invalid username format"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        validate_password_input(password)
    except Exception:
        return Response(
            {"error": True, "message": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    auth_result = authenticate_user(username, password)
    if not auth_result:
        return Response(
            {"error": True, "message": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, payload = issue_token(auth_result["username"], auth_result["role"])

    response = Response({
        "message": "Login successful",
        "user": {
            "username": auth_result["username"],
            "role": auth_result["role"],
        },
        "requiresPasswordChange": auth_result["requiresPasswordChange"],
    })

    secure_cookie = not django_settings.DEBUG
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        secure=secure_cookie,
        samesite="Lax" if not secure_cookie else "Strict",
        max_age=8 * 3600,
    )
    response.set_cookie(
        "token",
        token,
        httponly=True,
        secure=secure_cookie,
        samesite="Lax" if not secure_cookie else "Strict",
        max_age=8 * 3600,
    )

    return response


@extend_schema(
    responses={200: dict},
    summary="Logout and invalidate token",
    tags=["auth"],
)
@api_view(["POST"])
@permission_classes([IsJWTAuthenticated])
def logout_view(request):
    user = request.user
    revoke_token(user.jti, user.username)

    response = Response({"message": "Logged out successfully"})
    response.delete_cookie("auth_token")
    response.delete_cookie("token")
    response.delete_cookie("_csrf")
    return response


@extend_schema(
    request=PasswordChangeSerializer,
    responses={200: dict},
    summary="Change password",
    tags=["auth"],
)
@api_view(["POST"])
@permission_classes([IsJWTAuthenticated])
def change_password_view(request):
    serializer = PasswordChangeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    current_password = serializer.validated_data["currentPassword"]
    new_password = serializer.validated_data["newPassword"]

    # Validate new password meets policy
    try:
        validate_password(new_password)
    except Exception as e:
        return Response(
            {"error": True, "message": str(e.detail[0]) if hasattr(e, 'detail') else str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify current password
    auth_result = authenticate_user(request.user.username, current_password)
    if not auth_result:
        return Response(
            {"error": True, "message": "Current password is incorrect"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    change_password(request.user.username, request.user.role, new_password)

    return Response({"message": "Password changed successfully"})


@extend_schema(
    responses={200: dict},
    summary="Verify current authentication status",
    tags=["auth"],
)
@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def verify_view(request):
    user = request.user
    return Response({
        "authenticated": True,
        "user": {
            "username": user.username,
            "role": user.role,
        },
        "requiresPasswordChange": not has_custom_password(user.username),
    })


@extend_schema(
    responses={200: dict},
    summary="Get CSRF token",
    tags=["auth"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_token_view(request):
    csrf_token = secrets.token_hex(32)
    response = Response({"csrfToken": csrf_token})
    secure_cookie = not django_settings.DEBUG
    response.set_cookie(
        "_csrf",
        csrf_token,
        httponly=True,
        secure=secure_cookie,
        samesite="Lax" if not secure_cookie else "Strict",
        max_age=15 * 60,  # 15 minutes
    )
    return response


@extend_schema(
    responses={200: dict},
    summary="Health check",
    tags=["system"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_view(request):
    return Response({"status": "ok", "timestamp": time.time()})
