from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ghostnet.admin_api.deps import require_admin, store_of

router = APIRouter(dependencies=[Depends(require_admin)])


class PanicRequest(BaseModel):
    confirmation: str


@router.get("/panic")
def panic_status(request: Request) -> dict[str, bool]:
    return {"panic": store_of(request).panic_active()}


@router.post("/panic")
def panic(request: Request, body: PanicRequest) -> dict[str, Any]:
    if body.confirmation != "STOP GHOSTNET":
        raise HTTPException(400, "Explicit confirmation 'STOP GHOSTNET' is required")
    store_of(request).set_panic(True)
    return {
        "panic": True,
        "decoys_should_exit": True,
        "message": "Decoy agents poll the authenticated kill switch and exit.",
    }


@router.post("/admin/panic/reset")
def reset(request: Request, body: PanicRequest) -> dict[str, bool]:
    if body.confirmation != "RESET GHOSTNET":
        raise HTTPException(400, "Explicit confirmation 'RESET GHOSTNET' is required")
    store_of(request).set_panic(False)
    return {"panic": False}
