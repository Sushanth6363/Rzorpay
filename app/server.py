"""Combined public entrypoint: the dashboard AND the webhook listener on one port.

WHY THIS EXISTS
    A hosted deployment gets ONE public port per service, and a persistent disk can be
    mounted to exactly ONE service. The dashboard and the webhook listener share a single
    SQLite file, so they cannot be split into two services without also moving to a
    client/server database - which would be a rewrite of the whole DAL for a deployment
    detail.

    So they run in one process behind one port:

        POST /webhooks/razorpay   handled here, in-process, by the real listener
        GET  /health /feed /metrics   the listener's own operational endpoints
        everything else           reverse-proxied to Streamlit on 127.0.0.1:8501

    Streamlit is not an ASGI application - it runs its own Tornado server - so it cannot
    simply be mounted. It has to be spawned and proxied, including the WebSocket it uses
    for every interaction. A proxy that forwards HTTP but not `/_stcore/stream` produces
    the worst possible symptom: the page renders once and then silently ignores every
    click, which looks like a broken app rather than a broken proxy.

ORDER MATTERS
    The webhook route is registered BEFORE the catch-all. Starlette matches in order, so a
    catch-all registered first would swallow Razorpay's callbacks and hand them to
    Streamlit, which would answer 200 and drop them. Signed money events would vanish with
    no error anywhere.

SAFETY
    This changes only WHERE the engine runs, never WHAT IT MAY DO. Dispatch remains gated
    by RECOVERY_DISPATCH_ENABLED, which is false unless explicitly set. Read the note in
    render.yaml before enabling it on a public URL.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import httpx
import websockets
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import PlainTextResponse, StreamingResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.api.webhook_listener import _lifespan as listener_lifespan
from app.api.webhook_listener import routes as listener_routes

logger = logging.getLogger("recovery.server")

REPO_ROOT = Path(__file__).resolve().parents[1]

PUBLIC_PORT = int(os.environ.get("PORT", "10000"))
STREAMLIT_PORT = int(os.environ.get("STREAMLIT_INTERNAL_PORT", "8501"))
STREAMLIT_HOST = "127.0.0.1"
STREAMLIT_BASE = f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}"

# Hop-by-hop headers belong to a single connection and must not be forwarded. Passing
# `content-length` through after the body has been re-encoded is the classic way to make a
# proxied response hang until it times out.
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length",
    "content-encoding", "host",
}

_streamlit: Optional[subprocess.Popen] = None


def _streamlit_command() -> List[str]:
    """Streamlit, bound to loopback and configured for life behind a proxy."""
    return [
        sys.executable, "-m", "streamlit", "run", str(REPO_ROOT / "streamlit_app.py"),
        "--server.port", str(STREAMLIT_PORT),
        "--server.address", STREAMLIT_HOST,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        # Both must be off behind a proxy. Streamlit's XSRF check compares against an
        # origin it can no longer see, and would reject every upload - including the CSV
        # that drives the entire live demo.
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
    ]


async def _wait_for_streamlit(timeout: float = 90.0) -> bool:
    """Block until Streamlit accepts connections, or give up and say so."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            with socket.create_connection((STREAMLIT_HOST, STREAMLIT_PORT), timeout=1.0):
                return True
        except OSError:
            await asyncio.sleep(0.5)
    return False


@asynccontextmanager
async def lifespan(app: Starlette):
    """Start Streamlit alongside the listener's own lifespan, and stop it after."""
    global _streamlit

    logger.info("starting Streamlit on %s", STREAMLIT_BASE)
    _streamlit = subprocess.Popen(_streamlit_command(), cwd=str(REPO_ROOT))

    if await _wait_for_streamlit():
        logger.info("Streamlit is accepting connections")
    else:
        # Not fatal on purpose: the webhook endpoint is the half that must never be down.
        # A dashboard that failed to start should not stop money events being recorded.
        logger.error("Streamlit did not start in time - webhooks still served, UI will 502")

    app.state.client = httpx.AsyncClient(base_url=STREAMLIT_BASE, timeout=None)

    # The listener owns the background follow-up worker and the schema bootstrap. Compose
    # rather than reimplement, so this file cannot drift from the standalone entrypoint.
    async with listener_lifespan(app):
        try:
            yield
        finally:
            await app.state.client.aclose()
            if _streamlit and _streamlit.poll() is None:
                _streamlit.terminate()
                try:
                    _streamlit.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    _streamlit.kill()


def _forwardable(headers) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP}


async def proxy_http(request: Request):
    """Forward one HTTP request to Streamlit and stream the response back."""
    client: httpx.AsyncClient = request.app.state.client
    upstream = client.build_request(
        request.method,
        httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8")),
        headers=_forwardable(request.headers),
        content=request.stream(),
    )
    try:
        response = await client.send(upstream, stream=True)
    except httpx.ConnectError:
        return PlainTextResponse("Dashboard is still starting. Refresh in a moment.", 503)

    return StreamingResponse(
        response.aiter_raw(),
        status_code=response.status_code,
        headers=_forwardable(response.headers),
        background=BackgroundTask(response.aclose),
    )


async def proxy_ws(websocket: WebSocket):
    """Pump Streamlit's WebSocket both ways.

    Without this the page renders once and then ignores every interaction, because every
    Streamlit rerun travels over this socket.

    THE SUBPROTOCOL IS NOT OPTIONAL
        Streamlit's browser client opens `/_stcore/stream` requesting a subprotocol. A
        server that accepts without echoing one back completes the handshake and is then
        dropped by the client immediately - which surfaces as a page stuck on skeleton
        placeholders, with the only clue a bare "WebSocket connection failed" in a console
        nobody is looking at.

        So the upstream connection is opened FIRST, carrying whatever the browser asked
        for, and the client is accepted with the subprotocol the upstream actually chose.
        Opening upstream first has a second benefit: if Streamlit is not ready, the client
        is refused cleanly instead of being accepted into a socket with nothing behind it.
    """
    requested = list(websocket.scope.get("subprotocols") or [])

    target = f"ws://{STREAMLIT_HOST}:{STREAMLIT_PORT}{websocket.url.path}"
    if websocket.url.query:
        target = f"{target}?{websocket.url.query}"

    try:
        upstream = await websockets.connect(
            target,
            max_size=None,
            open_timeout=20,
            subprotocols=requested or None,
        )
    except Exception as exc:  # noqa: BLE001 - refusing cleanly matters more than the type
        logger.warning("upstream websocket refused (%s): %s", target, exc)
        await websocket.close(code=1011)
        return

    await websocket.accept(subprotocol=upstream.subprotocol)

    async def client_to_upstream() -> None:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return
            if (data := message.get("text")) is not None:
                await upstream.send(data)
            elif (data := message.get("bytes")) is not None:
                await upstream.send(data)

    async def upstream_to_client() -> None:
        async for frame in upstream:
            if isinstance(frame, bytes):
                await websocket.send_bytes(frame)
            else:
                await websocket.send_text(frame)

    tasks = {asyncio.create_task(client_to_upstream()),
             asyncio.create_task(upstream_to_client())}
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        # Retrieve exceptions from the finished side so a normal disconnect does not
        # surface as "Task exception was never retrieved" in the logs.
        for task in done:
            with_exc = task.exception()
            if with_exc and not isinstance(
                with_exc, (WebSocketDisconnect, websockets.exceptions.WebSocketException, OSError)
            ):
                logger.warning("websocket proxy error: %r", with_exc)
    finally:
        await upstream.close()
        try:
            await websocket.close()
        except RuntimeError:
            pass


# ORDER IS LOAD-BEARING. The listener's own routes are matched first; the catch-all last.
routes = [
    *listener_routes,
    WebSocketRoute("/{path:path}", endpoint=proxy_ws),
    Route(
        "/{path:path}",
        endpoint=proxy_http,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    ),
]

app = Starlette(debug=False, routes=routes, lifespan=lifespan)


if __name__ == "__main__":
    import uvicorn

    from app.realtime import config

    logging.basicConfig(level=logging.INFO)
    posture = config.describe()
    logger.info("Unified Recovery Engine - combined server")
    logger.info("  public port     : %s", PUBLIC_PORT)
    logger.info("  database        : %s", posture["db_path"])
    logger.info("  signature req'd : %s", posture["signature_required"])
    logger.info("  dispatch enabled: %s", posture["dispatch_enabled"])
    if not posture["dispatch_enabled"]:
        logger.info("  DRY RUN - decisions are recorded, nothing is sent to anyone.")

    uvicorn.run(app, host="0.0.0.0", port=PUBLIC_PORT)
