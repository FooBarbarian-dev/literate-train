"""Host relationship analyzer.

Finds pairs of hostnames that share IPs, domains, or usernames.
"""

from django.db.models import Q

from logs.models import Log
from relations.analyzers.base import upsert_relation


class HostAnalyzer:
    relationship_type = "host"

    @classmethod
    def analyze_log(cls, log):
        """Analyze a single log entry for host relations."""
        if not log.hostname:
            return 0

        # Build filter for logs sharing any overlapping attribute
        shared = Q()
        if log.internal_ip:
            shared |= Q(internal_ip=log.internal_ip)
        if log.external_ip:
            shared |= Q(external_ip=log.external_ip)
        if log.domain:
            shared |= Q(domain=log.domain)
        if log.username:
            shared |= Q(username=log.username)

        if not shared:
            return 0

        op_tags = cls._get_operation_tags(log)

        related = (
            Log.objects.filter(shared)
            .exclude(hostname="")
            .exclude(hostname=log.hostname)
            .values_list("hostname", flat=True)
            .distinct()
        )

        count = 0
        for other_hostname in related:
            # Normalize ordering to avoid duplicate pairs
            h1, h2 = sorted([log.hostname, other_hostname])
            upsert_relation(
                source_type="hostname",
                source_value=h1,
                target_type="hostname",
                target_value=h2,
                relationship_type="host",
                operation_tags=op_tags,
                log_id=log.id,
            )
            count += 1
        return count

    @classmethod
    def analyze_all(cls):
        """Analyze all logs for host relations."""
        count = 0
        for log in Log.objects.exclude(hostname="").iterator():
            count += cls.analyze_log(log)
        return count

    @classmethod
    def _get_operation_tags(cls, log):
        return list(
            log.tags.filter(name__startswith="OP:").values_list("name", flat=True)
        )
