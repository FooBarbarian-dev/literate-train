"""CLI entry points for the Clio relation service."""
import os
import sys


def _ensure_settings():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "relation_service.settings")


def server():
    """Start the relation service with gunicorn + uvicorn workers."""
    _ensure_settings()
    port = os.environ.get("PORT", "3002")
    workers = os.environ.get("WEB_CONCURRENCY", "2")
    sys.argv = [
        "gunicorn",
        "relation_service.asgi:application",
        "-w", workers,
        "-k", "uvicorn.workers.UvicornWorker",
        "--bind", f"0.0.0.0:{port}",
    ]
    from gunicorn.app.wsgiapp import run
    run()


def migrate():
    """Run database migrations."""
    _ensure_settings()
    from django.core.management import execute_from_command_line
    execute_from_command_line(["clio-relation", "migrate"])


def manage():
    """Passthrough to Django's manage.py."""
    _ensure_settings()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
