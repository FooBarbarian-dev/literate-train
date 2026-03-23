import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from logs.models import Log
from logs.tasks import notify_relation_service

logger = logging.getLogger(__name__)

RELATION_SERVICE_ENDPOINT = "https://relation-service:3002/api/notify/log-update"


@receiver(post_save, sender=Log)
def log_post_save(sender, instance, **kwargs):
    notify_relation_service.delay(
        payload={"event": "log_update"},
        endpoint=RELATION_SERVICE_ENDPOINT,
    )


@receiver(post_delete, sender=Log)
def log_post_delete(sender, instance, **kwargs):
    notify_relation_service.delay(
        payload={"event": "log_update"},
        endpoint=RELATION_SERVICE_ENDPOINT,
    )
