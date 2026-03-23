"""
Base Django settings for the Clio platform.
"""

from pathlib import Path

import environ

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, "django-insecure-change-me-in-production"),
    DJANGO_ALLOWED_HOSTS=(list, [""]),
    POSTGRES_DB=(str, "clio"),
    POSTGRES_USER=(str, "clio"),
    POSTGRES_PASSWORD=(str, "clio"),
    POSTGRES_HOST=(str, "localhost"),
    POSTGRES_PORT=(str, "5432"),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
    EVIDENCE_ROOT=(str, ""),
    DATA_ROOT=(str, ""),
    EXPORT_ROOT=(str, ""),
    JWT_SECRET=(str, ""),
    JWT_ALGORITHM=(str, "HS256"),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 30),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
)

environ.Env.read_env()  # reads .env if present

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DJANGO_DEBUG")

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third-party
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    # Project apps
    "accounts",
    "logs",
    "tags",
    "operations",
    "evidence",
    "api_keys",
    "ingest",
    "export",
    "sessions_mgmt",
    "templates_mgmt",
    "audit",
    "relations",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "common.middleware.SecurityHeadersMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "common.middleware.CustomCsrfMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.middleware.InputSanitizationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "pool": True,
        },
    }
}

# ---------------------------------------------------------------------------
# Cache (django-redis)
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ---------------------------------------------------------------------------
# Password validation - we use custom validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = []

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.JWTCookieAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "10/minute",
        "api_key": "500/hour",
        "export": "20/hour",
        "ingest": "60/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ---------------------------------------------------------------------------
# drf-spectacular
# ---------------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "Clio Platform API",
    "DESCRIPTION": "API documentation for the Clio platform.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/",
    "COMPONENT_SPLIT_REQUEST": True,
}

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Evidence / File storage paths
# ---------------------------------------------------------------------------

EVIDENCE_ROOT = env("EVIDENCE_ROOT", default=str(BASE_DIR / "evidence"))
DATA_ROOT = env("DATA_ROOT", default=str(BASE_DIR / "data"))
EXPORT_ROOT = env("EXPORT_ROOT", default=str(BASE_DIR / "exports"))

# ---------------------------------------------------------------------------
# JWT / Auth settings
# ---------------------------------------------------------------------------

JWT_SECRET = env("JWT_SECRET", default=SECRET_KEY)
JWT_ALGORITHM = env("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES")
JWT_REFRESH_TOKEN_LIFETIME_DAYS = env("JWT_REFRESH_TOKEN_LIFETIME_DAYS")

# ---------------------------------------------------------------------------
# Storage backends
# ---------------------------------------------------------------------------

# NOTE (PoC): Default storage uses the local filesystem. In production,
# switch to S3Boto3Storage with proper AWS credentials and add boto3 +
# django-storages to requirements.txt.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": EVIDENCE_ROOT,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------

CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/1")
CELERY_TASK_SERIALIZER = "json"
