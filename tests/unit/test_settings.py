from __future__ import annotations

import pytest

from ghostnet.core.settings import Settings


def test_require_secrets_accepts_long_values(tmp_path) -> None:
    settings = Settings(
        database=str(tmp_path / "x.sqlite"),
        hash_key="a" * 20,
        chain_key="b" * 20,
        ingest_secret="c" * 20,
        admin_token="d" * 20,
    )
    settings.require_secrets()
    assert settings.canaries() == {"gk_live_demo_web_4f2a"}


@pytest.mark.parametrize(
    "field,value",
    [
        ("hash_key", ""),
        ("chain_key", "change-me"),
        ("ingest_secret", "short"),
        ("admin_token", "replace-with-a-different-random-token"),
    ],
)
def test_require_secrets_fails_closed(tmp_path, field: str, value: str) -> None:
    values = {
        "hash_key": "a" * 20,
        "chain_key": "b" * 20,
        "ingest_secret": "c" * 20,
        "admin_token": "d" * 20,
    }
    values[field] = value
    settings = Settings(database=str(tmp_path / "x.sqlite"), **values)
    with pytest.raises(RuntimeError, match="Missing or placeholder"):
        settings.require_secrets()


def test_canary_list_is_split_and_trimmed(tmp_path) -> None:
    settings = Settings(database=str(tmp_path / "x.sqlite"), canary_tokens=" one, two ,, ")
    assert settings.canaries() == {"one", "two"}
