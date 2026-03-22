from typing import Optional
from django.db.models import Count

from operations.models import Operation, UserOperation
from common.redis_client import get_encrypted_redis


def create_operation(name: str, description: str, created_by: str) -> Operation:
    """Create operation - trigger auto-creates tag."""
    return Operation.objects.create(
        name=name,
        description=description or "",
        created_by=created_by,
    )


def assign_user_to_operation(
    username: str, operation_id: int, assigned_by: str, is_primary: bool = False
) -> UserOperation:
    """Assign user to operation."""
    if is_primary:
        UserOperation.objects.filter(username=username).update(is_primary=False)

    user_op, created = UserOperation.objects.update_or_create(
        username=username,
        operation_id=operation_id,
        defaults={"is_primary": is_primary, "assigned_by": assigned_by},
    )

    # Clear cache
    redis_client = get_encrypted_redis()
    redis_client.delete(f"user:{username}:operations")

    return user_op


def remove_user_from_operation(username: str, operation_id: int) -> bool:
    """Remove user from operation."""
    deleted, _ = UserOperation.objects.filter(
        username=username, operation_id=operation_id
    ).delete()

    redis_client = get_encrypted_redis()
    redis_client.delete(f"user:{username}:operations")
    redis_client.delete(f"user:{username}:active_operation")

    return deleted > 0


def set_active_operation(username: str, operation_id: int) -> bool:
    """Set user's active operation."""
    user_op = UserOperation.objects.filter(
        username=username, operation_id=operation_id
    ).first()

    if not user_op:
        return False

    from django.utils import timezone
    user_op.last_accessed = timezone.now()
    user_op.save(update_fields=["last_accessed"])

    redis_client = get_encrypted_redis()
    redis_client.set(f"user:{username}:active_operation", str(operation_id))
    redis_client.delete(f"user:{username}:operations")

    return True


def get_user_operations(username: str) -> list:
    """Get all operations for a user."""
    return (
        UserOperation.objects.filter(
            username=username, operation__is_active=True
        )
        .select_related("operation", "operation__tag")
        .order_by("-is_primary", "-last_accessed")
    )
