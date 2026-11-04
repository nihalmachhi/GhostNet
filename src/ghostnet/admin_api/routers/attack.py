from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends, Request

from ghostnet.admin_api.deps import enriched_sessions, require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/attack/heatmap")
def heatmap(request: Request) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    for session in enriched_sessions(request):
        for mapping in session["attack"]:
            counts[str(mapping["tactic"])] += 1
    return {"tactics": [{"tactic": name, "count": count} for name, count in sorted(counts.items())]}
