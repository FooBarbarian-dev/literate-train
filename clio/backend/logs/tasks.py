from celery import shared_task
import httpx


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def notify_relation_service(self, payload: dict, endpoint: str):
    try:
        httpx.post(endpoint, json=payload, timeout=5)
    except httpx.RequestError as exc:
        raise self.retry(exc=exc)
