from datetime import datetime, timezone
from typing import Optional

from django.db import models

from logs.encryption import encrypt_field
from logs.models import Log
from tags.models import LogTag
from common.redis_client import get_encrypted_redis


def create_log_with_encryption(serializer, user) -> Log:
    """Create log entry, encrypting secrets field."""
    data = serializer.validated_data

    if not data.get("timestamp"):
        data["timestamp"] = datetime.now(timezone.utc)

    # Encrypt secrets if provided
    secrets_value = data.get("secrets")
    if secrets_value:
        data["secrets"] = encrypt_field(secrets_value)

    log = Log.objects.create(analyst=user.username, **data)
    return log


def update_log_with_encryption(log: Log, data: dict, user) -> Log:
    """Update log entry, handling encryption and lock checks."""
    # Check lock
    if log.locked and log.locked_by != user.username and not user.is_admin:
        raise PermissionError("Log is locked by another user")

    # Encrypt secrets if being updated
    if "secrets" in data and data["secrets"]:
        data["secrets"] = encrypt_field(data["secrets"])

    for key, value in data.items():
        setattr(log, key, value)
    log.save()
    return log


def check_log_lock(log: Log, username: str, is_admin: bool) -> bool:
    """Returns True if the user can edit the log."""
    if not log.locked:
        return True
    if log.locked_by == username:
        return True
    if is_admin:
        return True
    return False


def toggle_lock(log: Log, username: str, is_admin: bool) -> Log:
    """Toggle lock on a log entry."""
    if log.locked:
        # Unlock: only lock holder or admin
        if log.locked_by != username and not is_admin:
            raise PermissionError("Cannot unlock: locked by another user")
        log.locked = False
        log.locked_by = ""
    else:
        log.locked = True
        log.locked_by = username
    log.save(update_fields=["locked", "locked_by", "updated_at"])
    return log


def auto_tag_with_operation(log_id: int, username: str) -> None:
    """Auto-tag log with user's active operation tag."""
    try:
        redis_client = get_encrypted_redis()
        active_op_tag_id = get_active_operation_tag(username)
        if active_op_tag_id:
            LogTag.objects.get_or_create(
                log_id=log_id,
                tag_id=active_op_tag_id,
                defaults={"tagged_by": username},
            )
    except Exception:
        pass  # Failure should not block log creation


def get_active_operation_tag(username: str) -> Optional[int]:
    """Get the tag ID of the user's active operation."""
    from operations.models import Operation, UserOperation

    redis_client = get_encrypted_redis()

    # Check Redis cache first
    cached = redis_client.get(f"user:{username}:active_operation")
    if cached:
        try:
            op_id = int(cached)
            op = Operation.objects.filter(id=op_id, is_active=True).first()
            if op and op.tag_id:
                return op.tag_id
        except (ValueError, TypeError):
            pass

    # Fallback: get from database
    user_op = (
        UserOperation.objects.filter(username=username, operation__is_active=True)
        .select_related("operation")
        .order_by("-is_primary", "-last_accessed")
        .first()
    )
    if user_op and user_op.operation.tag_id:
        return user_op.operation.tag_id
    return None
