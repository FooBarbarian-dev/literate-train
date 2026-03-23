from __future__ import annotations

import json
import os
from typing import Optional

import environ
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
import redis

env = environ.Env()


class EncryptedRedis:
    """Every value encrypted with AES-256-GCM. Caller never sees raw Redis."""

    def __init__(self, redis_client: redis.Redis, encryption_key_hex: str):
        self._redis = redis_client
        self._key = bytes.fromhex(encryption_key_hex)

    def _encrypt(self, plaintext: str) -> bytes:
        aesgcm = AESGCM(self._key)
        iv = os.urandom(12)
        ct = aesgcm.encrypt(iv, plaintext.encode(), None)
        return iv + ct

    def _decrypt(self, data: bytes) -> str:
        aesgcm = AESGCM(self._key)
        return aesgcm.decrypt(data[:12], data[12:], None).decode()

    def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        self._redis.set(key, self._encrypt(value), ex=ex)

    def get(self, key: str) -> Optional[str]:
        data = self._redis.get(key)
        return self._decrypt(data) if data else None

    def delete(self, key: str) -> None:
        self._redis.delete(key)

    def exists(self, key: str) -> bool:
        return self._redis.exists(key) > 0

    def keys(self, pattern: str) -> list[str]:
        return [k.decode() if isinstance(k, bytes) else k for k in self._redis.keys(pattern)]

    def sadd(self, key: str, *values: str) -> None:
        self._redis.sadd(key, *(self._encrypt(v) for v in values))

    def smembers(self, key: str) -> set[str]:
        raw = self._redis.smembers(key)
        return {self._decrypt(m) for m in raw} if raw else set()

    def srem(self, key: str, *values: str) -> None:
        existing = self._redis.smembers(key)
        for member in existing:
            try:
                if self._decrypt(member) in values:
                    self._redis.srem(key, member)
            except Exception:
                continue

    def expire(self, key: str, seconds: int) -> None:
        self._redis.expire(key, seconds)

    def ttl(self, key: str) -> int:
        return self._redis.ttl(key)

    def scan_iter(self, match: str) -> list[str]:
        return [k.decode() if isinstance(k, bytes) else k for k in self._redis.scan_iter(match=match)]


_encrypted_redis: Optional[EncryptedRedis] = None


def get_encrypted_redis() -> EncryptedRedis:
    global _encrypted_redis
    if _encrypted_redis is None:
        redis_password = env("REDIS_PASSWORD", default="")
        redis_host = env("REDIS_HOST", default="redis")
        redis_port = env.int("REDIS_PORT", default=6379)

        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            ssl=env.bool("REDIS_SSL", default=True),
            ssl_cert_reqs=None,
            decode_responses=False,
        )
        encryption_key = env("REDIS_ENCRYPTION_KEY", default="")
        _encrypted_redis = EncryptedRedis(redis_client, encryption_key)
    return _encrypted_redis
