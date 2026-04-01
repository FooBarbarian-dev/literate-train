from relations.analyzers.host import HostAnalyzer
from relations.analyzers.ip import IPAnalyzer
from relations.analyzers.domain import DomainAnalyzer
from relations.analyzers.user_command import UserCommandAnalyzer

ALL_ANALYZERS = [HostAnalyzer, IPAnalyzer, DomainAnalyzer, UserCommandAnalyzer]

__all__ = [
    "HostAnalyzer",
    "IPAnalyzer",
    "DomainAnalyzer",
    "UserCommandAnalyzer",
    "ALL_ANALYZERS",
]
