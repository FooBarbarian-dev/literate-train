import os
from typing import Optional

from accounts.hashers import hash_password, verify_password
from common.redis_client import get_encrypted_redis


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user. Returns dict with role info or None.

    Check order:
    1. Custom password in Redis (user:password:<username> or admin:password:<username>)
    2. Initial admin password from env
    3. Initial user password from env
    """
    redis_client = get_encrypted_redis()

    # Check for custom admin password
    admin_hash = redis_client.get(f"admin:password:{username}")
    if admin_hash:
        if verify_password(password, admin_hash):
            return {"username": username, "role": "admin", "requiresPasswordChange": False}
        return None  # Has custom password, don't fall through

    # Check for custom user password
    user_hash = redis_client.get(f"user:password:{username}")
    if user_hash:
        if verify_password(password, user_hash):
            return {"username": username, "role": "user", "requiresPasswordChange": False}
        return None  # Has custom password, don't fall through

    # Check initial admin password
    initial_admin = os.environ.get("ADMIN_PASSWORD", "")
    if initial_admin and password == initial_admin:
        return {"username": username, "role": "admin", "requiresPasswordChange": True}

    # Check initial user password
    initial_user = os.environ.get("USER_PASSWORD", "")
    if initial_user and password == initial_user:
        return {"username": username, "role": "user", "requiresPasswordChange": True}

    return None


def change_password(username: str, role: str, new_password: str) -> None:
    """Store new hashed password in Redis."""
    redis_client = get_encrypted_redis()
    hashed = hash_password(new_password)
    prefix = "admin" if role == "admin" else "user"
    redis_client.set(f"{prefix}:password:{username}", hashed)


def has_custom_password(username: str) -> bool:
    """Check if user has set a custom password."""
    redis_client = get_encrypted_redis()
    return (
        redis_client.exists(f"admin:password:{username}")
        or redis_client.exists(f"user:password:{username}")
    )
