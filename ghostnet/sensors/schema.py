from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventInput(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decoy_id: str
    decoy_type: str
    session_id: str
    src_hash: str
    src_port: int = Field(ge=0, le=65535)
    dst_port: int = Field(ge=0, le=65535)
    proto: str = "tcp"
    kind: str
    data: dict[str, Any] = Field(default_factory=dict)
    prev_hash: str = ""
    hash: str = ""
