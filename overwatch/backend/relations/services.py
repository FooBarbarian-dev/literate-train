"""Relation analysis orchestration."""

import logging

from django.db import connection

from logs.models import Log
from relations.analyzers import ALL_ANALYZERS
from relations.models import Relation

logger = logging.getLogger(__name__)


def analyze_log(log_id: int) -> dict[str, int]:
    """Run all analyzers for a single log entry. Returns counts by type."""
    try:
        log = Log.objects.get(id=log_id)
    except Log.DoesNotExist:
        logger.warning("analyze_log called for non-existent log %s", log_id)
        return {}

    results = {}
    for analyzer_cls in ALL_ANALYZERS:
        count = analyzer_cls.analyze_log(log)
        results[analyzer_cls.relationship_type] = count
    return results


def rebuild_all_relations() -> dict[str, int]:
    """Truncate all relations and rebuild from all logs."""
    Relation.objects.all().delete()

    results = {}
    for analyzer_cls in ALL_ANALYZERS:
        count = analyzer_cls.analyze_all()
        results[analyzer_cls.relationship_type] = count
        logger.info("Rebuilt %d %s relations", count, analyzer_cls.relationship_type)

    return results


def delete_relations_for_log(log_id: int) -> int:
    """Remove a log ID from all source_log_ids; delete empty relations."""
    with connection.cursor() as cursor:
        # Remove log_id from source_log_ids arrays
        cursor.execute(
            """
            UPDATE relations
            SET source_log_ids = array_remove(source_log_ids, %(log_id)s)
            WHERE %(log_id)s = ANY(source_log_ids)
            """,
            {"log_id": log_id},
        )

        # Delete relations with empty source_log_ids
        cursor.execute(
            """
            DELETE FROM relations
            WHERE source_log_ids = '{}'
            """
        )
        deleted = cursor.rowcount

    return deleted
