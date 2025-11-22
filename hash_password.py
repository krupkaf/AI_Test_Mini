#!/usr/bin/env python3
"""Generate bcrypt hash for a password.

Usage:
    uv run python hash_password.py <password>
    uv run python hash_password.py  # interactive mode
"""

import base64
import sys

import bcrypt


def hash_password(password: str) -> str:
    """Generate bcrypt hash for password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input("Enter password: ")

    hashed = hash_password(password)
    hashed_b64 = base64.b64encode(hashed.encode("utf-8")).decode("utf-8")

    print(f"\nBcrypt hash: {hashed}")
    print(f"Base64 encoded: {hashed_b64}")
    print(f'\nFor .env (local):  AUTH_USERS={{"user": "{hashed}"}}')
    print(f'For .env (Docker): AUTH_USERS={{"user": "{hashed_b64}"}}')
