"""Thin CLI wrappers exposed as console_scripts entry points."""

import os
import sys


def manage():
    """Entry point that mirrors ``python manage.py``."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.development")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
