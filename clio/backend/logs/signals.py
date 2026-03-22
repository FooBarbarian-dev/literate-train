import threading
import time
import logging

import httpx
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from logs.models import Log

logger = logging.getLogger(__name__)

_last_notification = 0
_notification_lock = threading.Lock()
DEBOUNCE_SECONDS = 5


def _notify_relation_service():
    """Send notification to relation service (debounced, fire-and-forget)."""
    global _last_notification

    with _notification_lock:
        now = time.time()
        if now - _last_notification < DEBOUNCE_SECONDS:
            return
        _last_notification = now

    def _send():
        try:
            httpx.post(
                "https://relation-service:3002/api/notify/log-update",
                json={"event": "log_update"},
                timeout=3.0,
                verify=False,
            )
        except Exception as e:
            logger.warning(f"Failed to notify relation service: {e}")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


@receiver(post_save, sender=Log)
def log_post_save(sender, instance, **kwargs):
    _notify_relation_service()


@receiver(post_delete, sender=Log)
def log_post_delete(sender, instance, **kwargs):
    _notify_relation_service()
