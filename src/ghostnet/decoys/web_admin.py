from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ghostnet.sensors.emitter import emit_payload
from ghostnet.sensors.privacy import credential_summary

MAX_BODY = 8192
DECOY = "web-admin-01"
BANNER = os.getenv("GHOSTNET_WEB_BANNER", "Operations Console")
CANARY = os.getenv("GHOSTNET_WEB_CANARY", "gk_live_demo_web_4f2a")

app = FastAPI(
    title="GhostNet web decoy",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    servers=[],
)


def _peer(request: Request) -> tuple[str, int]:
    client = request.client
    return (client.host, client.port) if client else ("unknown", 0)


async def _emit(request: Request, kind: str, data: Mapping[str, object]) -> None:
    source, port = _peer(request)
    await emit_payload(DECOY, "web-admin", source, port, 8081, kind, data)


async def _bounded_body(request: Request) -> bytes:
    declared = request.headers.get("content-length")
    if declared and (not declared.isdigit() or int(declared) > MAX_BODY):
        raise ValueError("body too large")
    body = await request.body()
    if len(body) > MAX_BODY:
        raise ValueError("body too large")
    return body


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> str:
    await _emit(
        request,
        "http_request",
        {"method": "GET", "path": "/", "user_agent": request.headers.get("user-agent", "")[:120]},
    )
    return (
        f"<html><title>{BANNER}</title><body><h1>{BANNER}</h1>"
        "<form method='post' action='/login'><input name='user'>"
        "<input name='password' type='password'></form>"
        f"<!-- API recovery key: {CANARY} --></body></html>"
    )


@app.post("/login")
async def login(request: Request) -> JSONResponse:
    try:
        raw = await _bounded_body(request)
        if "application/json" in request.headers.get("content-type", ""):
            body = await request.json()
        else:
            body = {key: values[-1] for key, values in parse_qs(raw.decode()).items()}
        if not isinstance(body, dict):
            raise ValueError("expected an object")
    except (ValueError, UnicodeDecodeError):
        return JSONResponse({"message": "Invalid request"}, status_code=400)
    user, password = str(body.get("user", "")), str(body.get("password", ""))
    data = dict(credential_summary(user, password))
    data.update({"method": "POST", "path": "/login"})
    await _emit(request, "auth_attempt", data)
    return JSONResponse({"message": "Invalid username or password"}, status_code=401)


@app.get("/recover")
async def recover(request: Request) -> dict[str, str]:
    await _emit(request, "http_request", {"method": "GET", "path": "/recover"})
    return {"status": "recovery request recorded"}


@app.get("/token/{token}")
async def token(request: Request, token: str) -> dict[str, str]:
    await _emit(request, "token_seen", {"token": token[:96], "path": "/token"})
    return {"status": "request recorded"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "decoy": DECOY}


if __name__ == "__main__":
    import asyncio

    import uvicorn

    from ghostnet.sensors.panic_poller import wait_for_panic

    async def main() -> None:
        server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="warning"))
        poller = asyncio.create_task(wait_for_panic(DECOY))
        try:
            await server.serve()
        finally:
            poller.cancel()

    asyncio.run(main())
