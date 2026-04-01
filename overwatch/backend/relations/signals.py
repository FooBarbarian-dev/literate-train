"""Signal handlers to trigger relation analysis on log changes."""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from logs.models import Log

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Log)
def analyze_log_on_save(sender, instance, **kwargs):
    """Analyze relations when a log is created or updated."""
    from relations.services import analyze_log

    try:
        analyze_log(instance.id)
    except Exception:
        logger.exception("Failed to analyze relations for log %s", instance.id)


@receiver(post_delete, sender=Log)
def cleanup_relations_on_delete(sender, instance, **kwargs):
    """Remove log references from relations when a log is deleted."""
    from relations.services import delete_relations_for_log

    try:
        delete_relations_for_log(instance.id)
    except Exception:
        logger.exception(
            "Failed to clean up relations for deleted log %s", instance.id
        )
