import base64
import hashlib
import os
from passlib.hash import pbkdf2_sha256


ITERATIONS = 310000
SALT_LENGTH = 32
KEY_LENGTH = 32


def hash_password(password: str) -> str:
    """Hash password with PBKDF2-SHA256, 310k iterations, 32-byte salt."""
    salt = os.urandom(SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, ITERATIONS, dklen=KEY_LENGTH
    )
    return base64.b64encode(salt + dk).decode()


def verify_password(password: str, stored_hash: str) -> bool:
    """Timing-safe comparison of password against stored hash."""
    try:
        decoded = base64.b64decode(stored_hash)
        salt = decoded[:SALT_LENGTH]
        stored_dk = decoded[SALT_LENGTH:]
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, ITERATIONS, dklen=KEY_LENGTH
        )
        return hmac_compare(dk, stored_dk)
    except Exception:
        return False


def hmac_compare(a: bytes, b: bytes) -> bool:
    """Timing-safe comparison."""
    import hmac as _hmac
    return _hmac.compare_digest(a, b)
