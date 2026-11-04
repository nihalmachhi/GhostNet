from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Iterable

PLACEHOLDER_KEYS = {"", "change-me", "local-demo-key-change-me", "replace-with-random-secret"}


def _key(secret: str | None = None) -> bytes:
    value = secret if secret is not None else os.getenv("GHOSTNET_HASH_KEY")
    if not value or value.strip().lower() in PLACEHOLDER_KEYS or len(value) < 16:
        raise RuntimeError("GHOSTNET_HASH_KEY must be configured; refusing to collect event data")
    return value.encode()


def keyed_hash(value: str, secret: str | None = None, *, length: int = 24) -> str:
    return hmac.new(_key(secret), value.encode(), hashlib.sha256).hexdigest()[:length]


def hash_source(address: str, secret: str | None = None) -> str:
    return "h:" + keyed_hash(address, secret)


def user_class(username: str) -> str:
    """Reduce a username to a coarse class; the raw value is never stored."""
    normalized = username.strip().lower()
    if normalized in {"root", "admin", "administrator"}:
        return "admin"
    if normalized in {"guest", "demo", "test", "user"}:
        return "default"
    return "other"


def credential_summary(
    username: str, password: str, secret: str | None = None
) -> dict[str, str | int]:
    """Return only keyed hashes, lengths and coarse categories."""
    normalized = password.lower()
    category = (
        "common_wordlist"
        if normalized in {"admin", "password", "123456", "letmein", "demo", "root"}
        else "other"
    )
    return {
        "user_hash": keyed_hash(username, secret, length=20),
        "user_len": len(username),
        "user_class": user_class(username),
        "password_len": len(password),
        "credential_hash": keyed_hash(password, secret, length=20),
        "category": category,
    }


def summarize_token(
    token: str, canaries: Iterable[str] = (), secret: str | None = None
) -> dict[str, str | int]:
    """Store a canary identifier only for an exact known canary; hash everything else."""
    known = {value for value in canaries if value}
    if token in known:
        return {"token_len": len(token), "canary_id": keyed_hash(token, secret, length=12)}
    return {"token_len": len(token), "token_hash": keyed_hash(token, secret, length=20)}
