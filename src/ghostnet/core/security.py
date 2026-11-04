from __future__ import annotations

import hashlib
import hmac


def decoy_token(secret: str, decoy_id: str) -> str:
    """Derive a per-decoy ingest token so one compromised decoy cannot impersonate another."""
    return hmac.new(secret.encode(), decoy_id.encode(), hashlib.sha256).hexdigest()


def verify_decoy_token(secret: str, decoy_id: str, supplied: str | None) -> bool:
    """Constant-time comparison of a supplied decoy token."""
    if not supplied:
        return False
    return hmac.compare_digest(decoy_token(secret, decoy_id), supplied)


def verify_admin_token(expected: str, supplied: str | None) -> bool:
    """Constant-time comparison of an admin token."""
    if not supplied:
        return False
    return hmac.compare_digest(expected, supplied)
