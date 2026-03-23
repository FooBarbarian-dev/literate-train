import pytest
from django.contrib import admin
from django.db import models

from logs.models import Log
from logs.services import toggle_lock
from logs.admin import LogAdmin


@pytest.mark.django_db
class TestLogServices:
    def test_toggle_unlock_does_not_crash(self, make_log):
        """Unlocking must set locked_by='' not None (catches regression)."""
        log = make_log(locked=True, locked_by="analyst1")
        result = toggle_lock(log, "analyst1", is_admin=False)
        assert result.locked is False
        assert result.locked_by == ""

    def test_log_admin_registered(self):
        """LogAdmin must be registered for Log model."""
        assert admin.site.is_registered(Log)

    def test_log_id_is_bigautofield(self):
        """Log pk must be BigAutoField (not AutoField)."""
        pk_field = Log._meta.get_field("id")
        assert isinstance(pk_field, models.BigAutoField)
