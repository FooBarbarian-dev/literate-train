"""
Production settings for the Overwatch platform.

NOTE (PoC): SSL redirect, HSTS, and secure cookie flags have been removed for
convenience. In production, re-enable:
  SECURE_SSL_REDIRECT = True
  SECURE_HSTS_SECONDS = 31536000
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SECURE_HSTS_PRELOAD = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
"""

from .base import *  # noqa: F401, F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# CORS - restrict in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
