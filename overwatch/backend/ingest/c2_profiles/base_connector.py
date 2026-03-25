"""
Base connector interface for live C2 server integration.

This module defines the abstract interface that future C2 connectors will
implement to pull real logs from running C2 servers (Sliver, Cobalt Strike,
Mythic, etc.) into Overwatch.

Usage (future):
    from ingest.c2_profiles.sliver_connector import SliverConnector

    connector = SliverConnector(
        host="10.0.50.5",
        port=31337,
        operator_config="/path/to/operator.cfg",
    )
    connector.connect()
    logs = connector.fetch_logs(since=last_sync)
    connector.disconnect()

NOTE: This is a scaffold for planned functionality. The static profile
generators (sliver.py, cobalt_strike.py) are used for demo/seed data.
Live connectors will inherit from ``BaseC2Connector`` once real C2 server
integration is implemented.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class BaseC2Connector(ABC):
    """Abstract base class for live C2 server log connectors."""

    def __init__(self, *, host, port, **kwargs):
        self.host = host
        self.port = port
        self.connected = False

    @abstractmethod
    def connect(self):
        """Establish connection to the C2 team server.

        Raises:
            ConnectionError: If the server is unreachable or auth fails.
        """

    @abstractmethod
    def disconnect(self):
        """Cleanly close the connection."""

    @abstractmethod
    def fetch_logs(self, *, since=None):
        """Pull operator logs from the C2 server.

        Args:
            since: Optional datetime — only return logs newer than this.
                   If None, return all available logs.

        Returns:
            list[dict]: Log entries in the same format as the static
            profile generators (matching ``Log`` model fields).
        """

    @abstractmethod
    def test_connection(self):
        """Verify the connection is alive and authenticated.

        Returns:
            bool: True if connection is healthy.
        """

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


class SliverConnector(BaseC2Connector):
    """Placeholder connector for Sliver C2 gRPC API.

    Sliver exposes a gRPC API for operators. This connector will use the
    ``sliver-py`` client library to authenticate with an operator config
    file and stream session/beacon events.

    Required config:
        - operator_config: Path to Sliver operator config file (.cfg)
        - host/port: Team server address (default: 31337)

    Dependencies (install when ready):
        pip install sliver-py grpcio
    """

    def __init__(self, *, host, port=31337, operator_config=None, **kwargs):
        super().__init__(host=host, port=port, **kwargs)
        self.operator_config = operator_config
        self._client = None

    def connect(self):
        # TODO: Implement with sliver-py
        # from sliver import SliverClientConfig, SliverClient
        # config = SliverClientConfig.parse_config_file(self.operator_config)
        # self._client = SliverClient(config)
        # await self._client.connect()
        raise NotImplementedError(
            "Live Sliver connector not yet implemented. "
            "Use 'python manage.py seed_c2_logs --profile sliver' for demo data."
        )

    def disconnect(self):
        if self._client:
            self._client = None
        self.connected = False

    def fetch_logs(self, *, since=None):
        raise NotImplementedError

    def test_connection(self):
        raise NotImplementedError


class CobaltStrikeConnector(BaseC2Connector):
    """Placeholder connector for Cobalt Strike Aggressor/Team Server logs.

    Cobalt Strike logs are typically found in the team server's data
    directory as text files (beacon logs, keystrokes, screenshots).
    This connector will parse those log files and/or use the Aggressor
    Script bridge to pull data.

    Approaches for integration:
        1. Parse team server log files directly (cobaltstrike/logs/)
        2. Use Aggressor Script's event_* hooks to stream to Overwatch API
        3. Use the External C2 spec for custom integrations

    Required config:
        - host/port: Team server address (default: 50050)
        - password: Team server password
        - log_directory: Path to CS logs (for file-based parsing)
    """

    def __init__(self, *, host, port=50050, password=None, log_directory=None, **kwargs):
        super().__init__(host=host, port=port, **kwargs)
        self.password = password
        self.log_directory = log_directory

    def connect(self):
        raise NotImplementedError(
            "Live Cobalt Strike connector not yet implemented. "
            "Use 'python manage.py seed_c2_logs --profile cobalt-strike' for demo data."
        )

    def disconnect(self):
        self.connected = False

    def fetch_logs(self, *, since=None):
        raise NotImplementedError

    def test_connection(self):
        raise NotImplementedError
