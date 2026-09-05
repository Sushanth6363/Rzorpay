"""The combined server must never hand a webhook to Streamlit.

WHY THIS TEST EXISTS
    `app/server.py` puts the dashboard and the webhook listener behind one public port,
    because a hosted service gets one port and a persistent disk mounts to one service.
    That is only safe if the route table is ordered correctly.

    Starlette matches routes IN ORDER. The proxy is a catch-all: `/{path:path}`. Registered
    before the listener's routes, it would swallow `POST /webhooks/razorpay`, forward it to
    Streamlit, and Streamlit would answer 200. Razorpay would see success, stop retrying,
    and the payment would never close its case. Signed money events would vanish with no
    error in any log.

    That failure is invisible in every other test, because every other test talks to the
    listener directly. This asserts the ordering itself.
"""

import pytest

from starlette.routing import Match

pytest.importorskip("httpx", reason="the combined server proxies with httpx")

from app import server  # noqa: E402
from app.api import webhook_listener  # noqa: E402


def _resolve(path: str, method: str = "GET", scope_type: str = "http"):
    """Return the route Starlette would actually pick for this request."""
    scope = {"type": scope_type, "path": path, "method": method, "headers": []}
    for route in server.app.router.routes:
        match, _ = route.matches(scope)
        if match == Match.FULL:
            return route
    return None


# --- the ordering that carries the money ----------------------------------------------------


def test_the_webhook_is_handled_in_process_not_proxied():
    """The whole reason this file exists."""
    route = _resolve("/webhooks/razorpay", method="POST")

    assert route is not None
    assert route.endpoint is webhook_listener.handle_razorpay_webhook
    assert route.endpoint is not server.proxy_http


def test_the_listener_operational_endpoints_are_not_proxied():
    for path in ("/health", "/feed", "/metrics"):
        route = _resolve(path)
        assert route is not None, path
        assert route.endpoint is not server.proxy_http, path


def test_everything_else_reaches_the_dashboard():
    for path in ("/", "/static/js/main.js", "/_stcore/host-config", "/anything/at/all"):
        route = _resolve(path)
        assert route is not None, path
        assert route.endpoint is server.proxy_http, path


def test_the_streamlit_websocket_is_proxied():
    """Without this the page renders once and then ignores every click."""
    route = _resolve("/_stcore/stream", scope_type="websocket")

    assert route is not None
    assert route.endpoint is server.proxy_ws


def test_the_catch_all_is_registered_last():
    """Pins the invariant directly, so reordering the list fails here rather than in
    production three weeks later."""
    endpoints = [getattr(r, "endpoint", None) for r in server.app.router.routes]

    assert endpoints[-1] is server.proxy_http
    assert endpoints.index(webhook_listener.handle_razorpay_webhook) < len(endpoints) - 1


# --- proxy hygiene ---------------------------------------------------------------------------


def test_hop_by_hop_headers_are_not_forwarded():
    """Forwarding content-length after re-encoding a body makes the response hang until it
    times out, which reads as "the dashboard is slow" rather than "the proxy is wrong"."""
    for header in ("connection", "transfer-encoding", "content-length", "upgrade", "host"):
        assert header in server.HOP_BY_HOP


def test_streamlit_is_launched_with_proxy_safe_settings():
    """Streamlit's XSRF check compares against an origin it cannot see behind a proxy and
    would reject every upload - including the CSV the whole live demo runs on."""
    command = " ".join(server._streamlit_command())

    assert "--server.enableXsrfProtection false" in command
    assert "--server.enableCORS false" in command
    assert f"--server.address {server.STREAMLIT_HOST}" in command


def test_streamlit_binds_to_loopback_only():
    """The subprocess must not be reachable from outside the container: it is the same app
    without the webhook routes, and would be a second, unauthenticated way in."""
    assert server.STREAMLIT_HOST == "127.0.0.1"
