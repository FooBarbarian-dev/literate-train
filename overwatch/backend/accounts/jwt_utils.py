import hashlib
import hmac as hmac_module
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import environ
import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from common.redis_client import get_encrypted_redis

env = environ.Env()

TOKEN_LIFETIME = 8 * 3600  # 8 hours in seconds
REFRESH_THRESHOLD = 0.75


def generate_admin_proof(username: str) -> str:
    """Generate HMAC-SHA256 admin proof."""
    secret = env("ADMIN_SECRET", default="")
    return hmac_module.new(
        secret.encode(), username.encode(), hashlib.sha256
    ).hexdigest()


def verify_admin_proof(username: str, proof: str) -> bool:
    """Verify HMAC admin proof."""
    expected = generate_admin_proof(username)
    return hmac_module.compare_digest(expected, proof)


def issue_token(username: str, role: str) -> tuple[str, dict]:
    """Issue JWT token. Returns (token_string, payload_dict)."""
    jti = uuid.uuid4().hex
    now = datetime.now(timezone.utc)

    admin_proof = generate_admin_proof(username) if role == "admin" else ""

    payload = {
        "jti": jti,
        "username": username,
        "role": role,
        "adminProof": admin_proof,
        "serverInstanceId": env("SERVER_INSTANCE_ID", default=""),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=TOKEN_LIFETIME)).timestamp()),
    }

    token = jwt.encode(payload, env("JWT_SECRET", default=""), algorithm="HS256")

    # Store in Redis
    redis_client = get_encrypted_redis()
    redis_value = f"username::{username}::role::{role}::issuedAt::{payload['iat']}"
    redis_client.set(f"jwt:{jti}", redis_value, ex=TOKEN_LIFETIME)
    redis_client.sadd(f"user:{username}:tokens", jti)

    return token, payload


def verify_token(token: str) -> dict:
    """7-step JWT verification per spec Section 3.1."""
    redis_client = get_encrypted_redis()

    # 1. Decode without verification to get JTI
    try:
        unverified = jwt.decode(
            token, options={"verify_signature": False, "verify_exp": False}
        )
    except jwt.DecodeError:
        raise AuthenticationFailed("Invalid token format")

    jti = unverified.get("jti")

    # 2. Check structure
    for required in ("jti", "exp", "iat"):
        if required not in unverified:
            raise AuthenticationFailed(f"Malformed token: missing {required}")

    # 3. Check expiration
    if datetime.now(timezone.utc).timestamp() > unverified["exp"]:
        raise AuthenticationFailed("Token expired")

    # 4. Check Redis (revocation)
    if not redis_client.exists(f"jwt:{jti}"):
        raise AuthenticationFailed("Token revoked")

    # 5. Verify signature
    try:
        payload = jwt.decode(
            token, env("JWT_SECRET", default=""), algorithms=["HS256"]
        )
    except jwt.InvalidSignatureError:
        raise AuthenticationFailed("Invalid token signature")
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")

    # 6. Verify server instance ID
    if payload.get("serverInstanceId") != env("SERVER_INSTANCE_ID", default=""):
        raise AuthenticationFailed("Token from previous server instance")

    # 7. Return user context
    return {
        "username": payload["username"],
        "role": payload["role"],
        "admin_proof": payload.get("adminProof", ""),
        "jti": jti,
    }


def should_refresh_token(payload: dict) -> bool:
    """Check if token has passed 75% of its lifetime."""
    now = time.time()
    iat = payload.get("iat", now)
    exp = payload.get("exp", now)
    total_lifetime = exp - iat
    elapsed = now - iat
    return elapsed >= total_lifetime * REFRESH_THRESHOLD


def refresh_token(username: str, role: str, old_jti: str) -> Optional[str]:
    """Issue new token and revoke old one."""
    redis_client = get_encrypted_redis()

    # Check if already refreshed
    if redis_client.exists(f"jwt:refreshed:{old_jti}"):
        return None

    # Issue new token
    new_token, new_payload = issue_token(username, role)

    # Mark old token as refreshed
    redis_client.set(f"jwt:refreshed:{old_jti}", new_payload["jti"], ex=60)

    # Remove old token
    redis_client.delete(f"jwt:{old_jti}")
    redis_client.srem(f"user:{username}:tokens", old_jti)

    return new_token


def revoke_token(jti: str, username: str) -> None:
    """Revoke a token by removing from Redis."""
    redis_client = get_encrypted_redis()
    redis_client.delete(f"jwt:{jti}")
    redis_client.srem(f"user:{username}:tokens", jti)


def revoke_all_user_tokens(username: str) -> int:
    """Revoke all tokens for a user."""
    redis_client = get_encrypted_redis()
    token_jtis = redis_client.smembers(f"user:{username}:tokens")
    count = 0
    for jti in token_jtis:
        redis_client.delete(f"jwt:{jti}")
        count += 1
    redis_client.delete(f"user:{username}:tokens")
    return count


def revoke_all_tokens() -> int:
    """Revoke all tokens globally."""
    redis_client = get_encrypted_redis()
    keys = redis_client.keys("jwt:*")
    count = 0
    for key in keys:
        if not key.startswith("jwt:refreshed:"):
            redis_client.delete(key)
            count += 1
    # Clear all user token sets
    user_keys = redis_client.keys("user:*:tokens")
    for key in user_keys:
        redis_client.delete(key)
    return count
