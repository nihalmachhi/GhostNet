from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, Request

from ghostnet.admin_api.deps import require_admin, store_of

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/integrity")
def integrity(request: Request) -> dict[str, Any]:
    return store_of(request).verify_integrity()


@router.get("/checkpoint")
def checkpoint(request: Request) -> dict[str, Any]:
    return cast(dict[str, Any], store_of(request).verify_integrity()["checkpoint"])
