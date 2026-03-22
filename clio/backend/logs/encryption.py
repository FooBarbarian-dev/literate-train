import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_field(plaintext: str) -> str:
    key = bytes.fromhex(os.environ.get("FIELD_ENCRYPTION_KEY", ""))
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
    ct, tag = ciphertext[:-16], ciphertext[-16:]
    return json.dumps({
        "encrypted": ct.hex(),
        "iv": iv.hex(),
        "authTag": tag.hex(),
        "type": "aes-256-gcm",
        "algorithm": "aes-256-gcm",
    })


def decrypt_field(stored: str) -> str:
    try:
        data = json.loads(stored)
        key = bytes.fromhex(os.environ.get("FIELD_ENCRYPTION_KEY", ""))
        aesgcm = AESGCM(key)
        iv = bytes.fromhex(data["iv"])
        ct = bytes.fromhex(data["encrypted"]) + bytes.fromhex(data["authTag"])
        return aesgcm.decrypt(iv, ct, None).decode()
    except Exception:
        return stored  # Return as-is if decryption fails
