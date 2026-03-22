"""CLI entry points for the Clio backend.

These are thin wrappers around Django management commands, exposed as
console_scripts via pyproject.toml so they're available on PATH after
``pip install -e .`` (or ``pip install clio-backend``).

Usage after install:
    clio-server          # Start the ASGI dev server
    clio-migrate         # Run database migrations
    clio-seed-passwords  # Hash and store initial passwords in Redis
    clio-seed-data       # Generate realistic C2 operator data
    clio-createsuperuser # Create a Django superuser
    clio-shell           # Open Django shell
"""
import os
import sys


def _ensure_settings():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.development")


def _run_management(*args):
    _ensure_settings()
    from django.core.management import execute_from_command_line
    execute_from_command_line(["clio"] + list(args))


def server():
    """Start the Clio backend with gunicorn + uvicorn workers."""
    _ensure_settings()
    port = os.environ.get("PORT", "3001")
    workers = os.environ.get("WEB_CONCURRENCY", "4")
    sys.argv = [
        "gunicorn",
        "backend.asgi:application",
        "-w", workers,
        "-k", "uvicorn.workers.UvicornWorker",
        "--bind", f"0.0.0.0:{port}",
    ]
    from gunicorn.app.wsgiapp import run
    run()


def dev_server():
    """Start the Django development server."""
    _run_management("runserver", "0.0.0.0:3001")


def migrate():
    """Run database migrations."""
    _run_management("migrate")


def make_migrations():
    """Create new migrations."""
    _run_management("makemigrations")


def seed_passwords():
    """Hash initial admin/user passwords and store in Redis."""
    _run_management("seed_initial_passwords")


def seed_data():
    """Generate realistic C2 operator data for the database."""
    _run_management("seed_c2_data", *sys.argv[1:])


def create_superuser():
    """Create a Django superuser."""
    _run_management("createsuperuser")


def shell():
    """Open the Django interactive shell."""
    _run_management("shell")


def manage():
    """Passthrough to Django's manage.py (accepts any subcommand)."""
    _ensure_settings()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


def test():
    """Run the test suite with pytest."""
    _ensure_settings()
    import pytest as _pytest
    sys.exit(_pytest.main(sys.argv[1:]))
