"""User-command relationship analyzer.

Creates username -> command relations directly from log entries.
"""

from logs.models import Log
from relations.analyzers.base import upsert_relation


class UserCommandAnalyzer:
    relationship_type = "user_command"

    @classmethod
    def analyze_log(cls, log):
        """Analyze a single log entry for user-command relations."""
        if not log.username or not log.command:
            return 0

        op_tags = cls._get_operation_tags(log)

        upsert_relation(
            source_type="username",
            source_value=log.username,
            target_type="command",
            target_value=log.command,
            relationship_type="user_command",
            operation_tags=op_tags,
            log_id=log.id,
        )
        return 1

    @classmethod
    def analyze_all(cls):
        count = 0
        for log in Log.objects.exclude(username="").exclude(command="").iterator():
            count += cls.analyze_log(log)
        return count

    @classmethod
    def _get_operation_tags(cls, log):
        return list(
            log.tags.filter(name__startswith="OP:").values_list("name", flat=True)
        )
