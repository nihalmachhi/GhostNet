from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventIn(BaseModel):
    """Untrusted event shape accepted from a decoy.

    The server assigns ``event_id``, ``ts``, ``seq``, ``prev_hash`` and ``hash``.
    Client-supplied integrity fields are rejected rather than silently ignored.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decoy_id: str = Field(min_length=1, max_length=80)
    decoy_type: str = Field(min_length=1, max_length=40)
    session_id: str = Field(min_length=1, max_length=120)
    src_hash: str = Field(min_length=3, max_length=80, pattern=r"^h:[0-9a-f]{16,64}$")
    src_port: int = Field(ge=0, le=65535)
    dst_port: int = Field(ge=0, le=65535)
    proto: str = Field(default="tcp", max_length=12)
    kind: str = Field(min_length=1, max_length=40)
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("data")
    @classmethod
    def bounded_data(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(str(value).encode()) > 4096:
            raise ValueError("event data exceeds 4096 bytes")
        return value


class EventStored(EventIn):
    """Server-owned event record returned by the store and API."""

    event_id: str = Field(min_length=32, max_length=32)
    ts: str
    seq: int = Field(ge=1)
    prev_hash: str
    hash: str = Field(min_length=64, max_length=64)


# Backwards-compatible alias for callers that used the old name.
EventInput = EventIn
