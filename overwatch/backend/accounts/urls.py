from django.urls import path

app_name = "accounts"

from accounts.views import (
    login_view,
    logout_view,
    change_password_view,
    verify_view,
    csrf_token_view,
    health_view,
)
from accounts.htmx_views import (
    login_page,
    auth_login_htmx,
    auth_logout_htmx,
)
from accounts.settings_htmx_views import (
    settings_page,
    change_password_htmx,
    logout_all_htmx,
)

urlpatterns = [
    # HTMX UI Routes
    path("login/", login_page, name="login-page"),
    path("htmx/login/", auth_login_htmx, name="auth-login-htmx"),
    path("htmx/logout/", auth_logout_htmx, name="auth-logout-htmx"),

    # Settings HTMX Routes
    path("settings/", settings_page, name="settings-page"),
    path("htmx/settings/change-password/", change_password_htmx, name="change-password-htmx"),
    path("htmx/settings/logout-all/", logout_all_htmx, name="logout-all-htmx"),

    # API Routes
    path("api/login/", login_view, name="auth-login-api"),
    path("api/logout/", logout_view, name="auth-logout-api"),
    path("change-password/", change_password_view, name="auth-change-password"),
    path("verify/", verify_view, name="auth-verify"),
    path("csrf-token/", csrf_token_view, name="csrf-token"),
    path("health/", health_view, name="health"),
]
