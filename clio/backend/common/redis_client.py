from __future__ import annotations

# NOTE (PoC): SSL transport and AES-256-GCM at-rest encryption have been removed
# from the Redis client for simplicity. All values are stored in plaintext.
# In production, re-enable ssl=True, ssl_cert_reqs, and the EncryptedRedis wrapper
# (see git history). This is intentionally insecure for local PoC use only.

from typing import Optional

import environ
import redis

env = environ.Env()


class RedisClient:
    """Thin wrapper around redis.Redis providing a consistent interface."""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        self._redis.set(key, value, ex=ex)

    def get(self, key: str) -> Optional[str]:
        data = self._redis.get(key)
        return data.decode() if isinstance(data, bytes) else data

    def delete(self, key: str) -> None:
        self._redis.delete(key)

    def exists(self, key: str) -> bool:
        return self._redis.exists(key) > 0

    def keys(self, pattern: str) -> list[str]:
        return [k.decode() if isinstance(k, bytes) else k for k in self._redis.keys(pattern)]

    def sadd(self, key: str, *values: str) -> None:
        self._redis.sadd(key, *values)

    def smembers(self, key: str) -> set[str]:
        raw = self._redis.smembers(key)
        return {m.decode() if isinstance(m, bytes) else m for m in raw} if raw else set()

    def srem(self, key: str, *values: str) -> None:
        self._redis.srem(key, *values)

    def expire(self, key: str, seconds: int) -> None:
        self._redis.expire(key, seconds)

    def ttl(self, key: str) -> int:
        return self._redis.ttl(key)

    def scan_iter(self, match: str) -> list[str]:
        return [k.decode() if isinstance(k, bytes) else k for k in self._redis.scan_iter(match=match)]


_redis_client: Optional[RedisClient] = None


def get_encrypted_redis() -> RedisClient:
    # NOTE (PoC): Function name kept for compatibility. No longer encrypted.
    global _redis_client
    if _redis_client is None:
        redis_password = env("REDIS_PASSWORD", default="")
        redis_host = env("REDIS_HOST", default="redis")
        redis_port = env.int("REDIS_PORT", default=6379)

        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=False,
        )
        _redis_client = RedisClient(client)
    return _redis_client
