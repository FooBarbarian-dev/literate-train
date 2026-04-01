"""IP relationship analyzer.

Finds pairs of IPs that share hostnames or domains.
"""

from django.db.models import Q

from logs.models import Log
from relations.analyzers.base import upsert_relation


class IPAnalyzer:
    relationship_type = "ip"

    @classmethod
    def analyze_log(cls, log):
        """Analyze a single log entry for IP relations."""
        ips = set()
        if log.internal_ip:
            ips.add(("internal", log.internal_ip))
        if log.external_ip:
            ips.add(("external", log.external_ip))

        if not ips:
            return 0

        shared = Q()
        if log.hostname:
            shared |= Q(hostname=log.hostname)
        if log.domain:
            shared |= Q(domain=log.domain)

        if not shared:
            return 0

        op_tags = cls._get_operation_tags(log)
        log_ips = {ip for _, ip in ips}

        # Find other logs sharing hostname/domain but having different IPs
        other_logs = (
            Log.objects.filter(shared)
            .exclude(id=log.id)
            .values("internal_ip", "external_ip")
            .distinct()
        )

        other_ips = set()
        for row in other_logs:
            if row["internal_ip"] and row["internal_ip"] not in log_ips:
                other_ips.add(row["internal_ip"])
            if row["external_ip"] and row["external_ip"] not in log_ips:
                other_ips.add(row["external_ip"])

        count = 0
        for log_ip in log_ips:
            for other_ip in other_ips:
                ip1, ip2 = sorted([log_ip, other_ip])
                upsert_relation(
                    source_type="ip",
                    source_value=ip1,
                    target_type="ip",
                    target_value=ip2,
                    relationship_type="ip",
                    operation_tags=op_tags,
                    log_id=log.id,
                )
                count += 1
        return count

    @classmethod
    def analyze_all(cls):
        count = 0
        for log in Log.objects.filter(
            Q(internal_ip__gt="") | Q(external_ip__gt="")
        ).iterator():
            count += cls.analyze_log(log)
        return count

    @classmethod
    def _get_operation_tags(cls, log):
        return list(
            log.tags.filter(name__startswith="OP:").values_list("name", flat=True)
        )
