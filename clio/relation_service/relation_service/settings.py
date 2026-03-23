"""
Django settings for relation_service project.
"""

from pathlib import Path

import environ

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, "django-insecure-change-me-in-production"),
    DJANGO_ALLOWED_HOSTS=(list, ["*"]),
    DB_NAME=(str, "clio"),
    DB_USER=(str, "clio"),
    DB_PASSWORD=(str, "clio"),
    DB_HOST=(str, "localhost"),
    DB_PORT=(str, "5432"),
)

environ.Env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env("DJANGO_DEBUG")

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "relations",
    "file_tracking",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "relation_service.urls"

WSGI_APPLICATION = "relation_service.wsgi.application"
ASGI_APPLICATION = "relation_service.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ---------------------------------------------------------------------------
# drf-spectacular
# ---------------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "Clio Relation Service API",
    "DESCRIPTION": "API for managing relations, file tracking, and log relationships.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
