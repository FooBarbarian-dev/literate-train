from typing import Optional
from tags.models import Tag, LogTag


def get_or_create_tag(name: str, created_by: str = "system") -> Tag:
    """Get existing tag or create with defaults."""
    name = name.strip().lower()
    tag, created = Tag.objects.get_or_create(
        name=name,
        defaults={
            "color": "#6B7280",
            "category": "custom",
            "created_by": created_by,
        },
    )
    return tag


def is_operation_tag(tag: Tag) -> bool:
    """Check if tag is a protected operation tag."""
    return tag.category == "operation" and tag.name.startswith("op:")


def add_tag_to_log(log_id: int, tag_id: int, tagged_by: str) -> LogTag:
    """Add a tag to a log entry."""
    log_tag, _ = LogTag.objects.get_or_create(
        log_id=log_id,
        tag_id=tag_id,
        defaults={"tagged_by": tagged_by},
    )
    return log_tag


def remove_tag_from_log(log_id: int, tag_id: int) -> bool:
    """Remove a tag from a log, protecting native operation tag."""
    log_tag = LogTag.objects.filter(log_id=log_id, tag_id=tag_id).first()
    if not log_tag:
        return False

    tag = log_tag.tag
    if is_operation_tag(tag):
        # Check if this is the first (native) operation tag
        first_op_tag = (
            LogTag.objects.filter(log_id=log_id, tag__category="operation", tag__name__startswith="op:")
            .order_by("tagged_at")
            .first()
        )
        if first_op_tag and first_op_tag.tag_id == tag_id:
            return False  # Cannot remove native operation tag

    log_tag.delete()
    return True


def remove_all_tags_from_log(log_id: int) -> int:
    """Remove all tags except native operation tag."""
    first_op_tag = (
        LogTag.objects.filter(log_id=log_id, tag__category="operation", tag__name__startswith="op:")
        .order_by("tagged_at")
        .first()
    )

    qs = LogTag.objects.filter(log_id=log_id)
    if first_op_tag:
        qs = qs.exclude(id=first_op_tag.id)

    count = qs.count()
    qs.delete()
    return count
