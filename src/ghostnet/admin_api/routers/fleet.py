from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from ghostnet.admin_api.deps import require_admin, store_of

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/fleet")
def fleet(request: Request) -> dict[str, Any]:
    store = store_of(request)
    return {
        "decoys": [
            {"id": item, "status": "configured", "interaction": "low"}
            for item in ("web-admin-01", "fake-ssh-01", "fake-db-01")
        ],
        "event_count": store.count(),
        "panic": store.panic_active(),
        "containment": {
            "network": "internal deception network",
            "host_bindings": "loopback-only edge proxy",
            "admin_api": "control network only",
        },
    }
