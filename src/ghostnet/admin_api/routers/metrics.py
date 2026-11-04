from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from ghostnet.admin_api.deps import require_admin, store_of

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/metrics", response_class=PlainTextResponse)
def metrics(request: Request) -> str:
    store = store_of(request)
    return (
        "# HELP ghostnet_events_total Retained event count.\n"
        "# TYPE ghostnet_events_total gauge\n"
        f"ghostnet_events_total {store.count()}\n"
        "# HELP ghostnet_panic Whether the panic switch is active.\n"
        "# TYPE ghostnet_panic gauge\n"
        f"ghostnet_panic {1 if store.panic_active() else 0}\n"
    )
