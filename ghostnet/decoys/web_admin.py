from __future__ import annotations

import os
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ghostnet.sensors.client import credential_summary, send_event

app = FastAPI(title="GhostNet web-admin decoy", docs_url=None, redoc_url=None, openapi_url=None)
DECOY = "web-admin-01"
CANARY = os.getenv("GHOSTNET_WEB_CANARY", "gk_live_demo_web_4f2a")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> str:
    await send_event(
        request,
        DECOY,
        "web-admin",
        "http_request",
        {"method": "GET", "path": "/", "user_agent": request.headers.get("user-agent", "")[:120]},
    )
    return f"<html><title>Operations Console</title><body><h1>Operations Console</h1><form method='post' action='/login'><input name='user'><input name='password' type='password'></form><!-- API recovery key: {CANARY} --></body></html>"


@app.post("/login")
async def login(request: Request) -> JSONResponse:
    if "application/json" in request.headers.get("content-type", ""):
        body = await request.json()
    else:
        body = {
            key: values[-1] for key, values in parse_qs((await request.body()).decode()).items()
        }
    user, password = str(body.get("user", "")), str(body.get("password", ""))
    data = credential_summary(user, password)
    data.update({"method": "POST", "path": "/login"})
    await send_event(request, DECOY, "web-admin", "auth_attempt", data)
    return JSONResponse({"message": "Invalid username or password"}, status_code=401)


@app.get("/recover")
async def recover(request: Request) -> dict[str, str]:
    await send_event(
        request, DECOY, "web-admin", "http_request", {"method": "GET", "path": "/recover"}
    )
    return {"status": "recovery request recorded"}


@app.get("/token/{token}")
async def token(request: Request, token: str) -> dict[str, str]:
    await send_event(
        request, DECOY, "web-admin", "token_seen", {"token": token[:96], "path": "/token"}
    )
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
        poller = asyncio.create_task(wait_for_panic())
        try:
            await server.serve()
        finally:
            poller.cancel()

    asyncio.run(main())
