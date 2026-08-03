"""
Password hashing and token generation using only Python's built-in libraries
(hashlib + secrets) — no extra packages needed.
"""

import hashlib
import secrets


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Returns (password_hash, salt). Generates a new salt if none given."""
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return pw_hash, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, expected_hash)


def generate_token() -> str:
    return secrets.token_hex(32)
