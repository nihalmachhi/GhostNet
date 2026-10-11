from __future__ import annotations

import hashlib
import hmac
import os


def hash_source(address: str, secret: str | None = None) -> str:
    key = (secret or os.getenv("GHOSTNET_HASH_KEY", "local-demo-key-change-me")).encode()
    digest = hmac.new(key, address.encode(), hashlib.sha256).hexdigest()[:24]
    return "h:" + digest


def credential_summary(
    username: str, password: str, secret: str | None = None
) -> dict[str, str | int]:
    key = (secret or os.getenv("GHOSTNET_HASH_KEY", "local-demo-key-change-me")).encode()
    digest = hmac.new(key, password.encode(), hashlib.sha256).hexdigest()[:20]
    normalized = password.lower()
    category = (
        "common_wordlist"
        if normalized in {"admin", "password", "123456", "letmein", "demo"}
        else "other"
    )
    return {
        "user": username[:80],
        "password_len": len(password),
        "password_hash": digest,
        "category": category,
    }
