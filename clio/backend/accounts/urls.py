from django.urls import path

from accounts.views import (
    login_view,
    logout_view,
    change_password_view,
    verify_view,
    csrf_token_view,
    health_view,
)

urlpatterns = [
    path("login/", login_view, name="auth-login"),
    path("logout/", logout_view, name="auth-logout"),
    path("change-password/", change_password_view, name="auth-change-password"),
    path("verify/", verify_view, name="auth-verify"),
    path("csrf-token/", csrf_token_view, name="csrf-token"),
    path("health/", health_view, name="health"),
]
