"""Base analyzer with raw SQL UPSERT for relation records."""

from django.db import connection


def upsert_relation(
    *,
    source_type: str,
    source_value: str,
    target_type: str,
    target_value: str,
    relationship_type: str,
    operation_tags: list[str] | None = None,
    log_id: int | None = None,
    metadata: dict | None = None,
):
    """Insert or update a relation using raw SQL with array deduplication.

    On conflict (source_type, source_value, target_type, target_value):
    - Increments strength and connection_count
    - Updates last_seen
    - Merges operation_tags (deduplicated)
    - Merges source_log_ids (deduplicated)
    - Updates metadata (shallow merge)
    """
    if operation_tags is None:
        operation_tags = []
    if metadata is None:
        metadata = {}

    log_ids = [log_id] if log_id else []

    sql = """
        INSERT INTO relations
            (source_type, source_value, target_type, target_value,
             relationship_type, strength, connection_count,
             first_seen, last_seen, operation_tags, source_log_ids, metadata)
        VALUES
            (%(source_type)s, %(source_value)s, %(target_type)s, %(target_value)s,
             %(relationship_type)s, 1, 1,
             NOW(), NOW(), %(operation_tags)s, %(log_ids)s, %(metadata)s)
        ON CONFLICT (source_type, source_value, target_type, target_value)
        DO UPDATE SET
            strength = relations.strength + 1,
            connection_count = relations.connection_count + 1,
            last_seen = NOW(),
            operation_tags = (
                SELECT ARRAY(SELECT DISTINCT unnest(
                    relations.operation_tags || EXCLUDED.operation_tags
                ))
            ),
            source_log_ids = (
                SELECT ARRAY(SELECT DISTINCT unnest(
                    relations.source_log_ids || EXCLUDED.source_log_ids
                ))
            ),
            metadata = relations.metadata || EXCLUDED.metadata
    """

    params = {
        "source_type": source_type,
        "source_value": source_value,
        "target_type": target_type,
        "target_value": target_value,
        "relationship_type": relationship_type,
        "operation_tags": operation_tags,
        "log_ids": log_ids,
        "metadata": metadata,
    }

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
