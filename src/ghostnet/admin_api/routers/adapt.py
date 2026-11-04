from __future__ import annotations

import json
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ghostnet.adapt.bandit import EpsilonGreedyPolicy
from ghostnet.adapt.policy import Action, approve
from ghostnet.admin_api.deps import enriched_sessions, require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


class AdaptDecision(BaseModel):
    action_id: str = Field(min_length=1, max_length=80)
    approve: bool = False
    reason: str = Field(default="Analyst-reviewed proposal", max_length=200)


def _bandit(request: Request) -> EpsilonGreedyPolicy:
    return request.app.state.bandit  # type: ignore[no-any-return]


@router.get("/adapt/propose")
def propose(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    rows = enriched_sessions(request)
    context = str(rows[-1]["class_label"]) if rows else "quiet"
    actions = [
        Action(
            uuid.uuid4().hex,
            kind,
            "web-admin",
            f"Safe response to {context}",
            {"delay_ms": 80} if kind == "response_delay_ms" else {},
        )
        for kind in ("rotate_fake_credential", "add_lure", "change_banner", "response_delay_ms")
    ]
    selected = _bandit(request).propose(context, actions)
    allowed, reason = approve(selected)
    expires_at = time.time() + settings.proposal_ttl_seconds
    request.app.state.store.save_proposal(
        selected.action_id,
        selected.kind,
        selected.decoy_type,
        selected.reason,
        selected.parameters,
        settings.proposal_ttl_seconds,
    )
    return {
        "action": {
            "action_id": selected.action_id,
            "kind": selected.kind,
            "decoy_type": selected.decoy_type,
            "reason": selected.reason,
            "parameters": selected.parameters,
        },
        "context": context,
        "policy_approved": allowed,
        "policy_reason": reason,
        "requires_analyst_approval": True,
        "expires_at": expires_at,
    }


@router.post("/adapt/approve")
def decide(request: Request, decision: AdaptDecision) -> dict[str, Any]:
    store = request.app.state.store
    proposal = store.get_proposal(decision.action_id)
    if proposal is None:
        raise HTTPException(404, "Unknown or expired proposal")
    if proposal["status"] != "pending":
        raise HTTPException(409, "Proposal was already decided")
    if float(proposal["expires_at"]) < time.time():
        store.decide_proposal(decision.action_id, "expired")
        raise HTTPException(410, "Proposal expired")

    parameters = json.loads(proposal["parameters_json"])
    action = Action(
        proposal["action_id"],
        proposal["kind"],
        proposal["decoy_type"],
        proposal["reason"],
        parameters,
    )
    allowed, reason = approve(action)
    accepted = decision.approve and allowed
    store.record_adaptation(
        action.action_id, json.dumps(action.__dict__, sort_keys=True), accepted, reason
    )
    _bandit(request).update(action, 1.0 if accepted else 0.0, context=decision.reason)
    store.decide_proposal(action.action_id, "approved" if accepted else "rejected")
    return {
        "action_id": action.action_id,
        "approved": accepted,
        "policy_approved": allowed,
        "reason": reason,
        "deployed": False,
    }
