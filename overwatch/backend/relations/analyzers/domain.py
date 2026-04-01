"""Domain relationship analyzer.

Finds pairs of domains that share IPs or hostnames.
"""

from django.db.models import Q

from logs.models import Log
from relations.analyzers.base import upsert_relation


class DomainAnalyzer:
    relationship_type = "domain"

    @classmethod
    def analyze_log(cls, log):
        """Analyze a single log entry for domain relations."""
        if not log.domain:
            return 0

        shared = Q()
        if log.internal_ip:
            shared |= Q(internal_ip=log.internal_ip)
        if log.external_ip:
            shared |= Q(external_ip=log.external_ip)
        if log.hostname:
            shared |= Q(hostname=log.hostname)

        if not shared:
            return 0

        op_tags = cls._get_operation_tags(log)

        related = (
            Log.objects.filter(shared)
            .exclude(domain="")
            .exclude(domain=log.domain)
            .values_list("domain", flat=True)
            .distinct()
        )

        count = 0
        for other_domain in related:
            d1, d2 = sorted([log.domain, other_domain])
            upsert_relation(
                source_type="domain",
                source_value=d1,
                target_type="domain",
                target_value=d2,
                relationship_type="domain",
                operation_tags=op_tags,
                log_id=log.id,
            )
            count += 1
        return count

    @classmethod
    def analyze_all(cls):
        count = 0
        for log in Log.objects.exclude(domain="").iterator():
            count += cls.analyze_log(log)
        return count

    @classmethod
    def _get_operation_tags(cls, log):
        return list(
            log.tags.filter(name__startswith="OP:").values_list("name", flat=True)
        )
