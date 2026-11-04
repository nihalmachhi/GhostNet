from __future__ import annotations

import json

import pytest

from ghostnet.sensors.privacy import (
    credential_summary,
    hash_source,
    keyed_hash,
    summarize_token,
    user_class,
)

SECRET = "unit-test-secret-value-1234"  # noqa: S105


def test_credentials_never_retain_raw_values() -> None:
    result = credential_summary("root", "super-secret-demo", SECRET)
    serialized = json.dumps(result)
    assert "super-secret-demo" not in serialized
    assert result["password_len"] == 17
    assert result["user_class"] == "admin"
    assert result["category"] == "other"
    assert credential_summary("root", "password", SECRET)["category"] == "common_wordlist"


def test_hashes_are_stable_and_keyed() -> None:
    assert hash_source("127.0.0.1", SECRET) == hash_source("127.0.0.1", SECRET)
    assert hash_source("127.0.0.1", SECRET) != hash_source("127.0.0.1", SECRET + "x")
    assert keyed_hash("x", SECRET, length=8) != keyed_hash("y", SECRET, length=8)


def test_user_class_categories() -> None:
    assert user_class("ROOT") == "admin"
    assert user_class("guest") == "default"
    assert user_class("alice") == "other"


def test_known_canary_gets_an_identifier_and_unknown_token_is_hashed() -> None:
    known = summarize_token("canary-value", {"canary-value"}, SECRET)
    unknown = summarize_token("random-token", {"canary-value"}, SECRET)
    assert "canary_id" in known and "token_hash" not in known
    assert "token_hash" in unknown and "canary_id" not in unknown


@pytest.mark.parametrize("value", ["", "change-me", "short"])
def test_privacy_key_fails_closed(value: str) -> None:
    with pytest.raises(RuntimeError):
        keyed_hash("x", value)
