from __future__ import annotations

import hashlib
import hmac
import os


def _key(secret: str | None = None) -> bytes:
    value = secret if secret is not None else os.getenv("GHOSTNET_HASH_KEY")
    if not value or value in {"local-demo-key-change-me", "change-me"}:
        raise RuntimeError("GHOSTNET_HASH_KEY must be configured; refusing to collect event data")
    return value.encode()


def keyed_hash(value: str, secret: str | None = None, *, length: int = 24) -> str:
    return hmac.new(_key(secret), value.encode(), hashlib.sha256).hexdigest()[:length]


def hash_source(address: str, secret: str | None = None) -> str:
    return "h:" + keyed_hash(address, secret)


def credential_summary(
    username: str, password: str, secret: str | None = None
) -> dict[str, str | int]:
    normalized = password.lower()
    category = (
        "common_wordlist"
        if normalized in {"admin", "password", "123456", "letmein", "demo"}
        else "other"
    )
    return {
        "user_hash": keyed_hash(username, secret, length=20),
        "user_len": len(username),
        "password_len": len(password),
        "credential_hash": keyed_hash(password, secret, length=20),
        "category": category,
    }
