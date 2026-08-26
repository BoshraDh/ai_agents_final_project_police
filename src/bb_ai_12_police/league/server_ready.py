"""Block until our own MCP route actually answers, not merely until it binds.

Found live 2026-08-26 vs SMNGRP05: `cli/league_peer.py` started the server
thread and then slept a flat 1.0s before beginning the protocol. Uvicorn
accepts connections a beat before FastMCP's `/mcp` route is mounted, so the
opponent's first `receive_turn` came back **404** while we looked, from the
outside, entirely up.

That lost turn is not recoverable by a retry: the opponent re-sends it on a
fresh session, but by then the two step counters are offset by one, and both
peers sit waiting for a turn the other already believes it sent. Sub-games 2
and 3 died in exactly that way -- we sent 3 turns, they sent 2 steps, then 180
seconds of mutual silence. Sub-game 1 survived only because the opponent had
been retrying against us for ~90s beforehand, so their first success landed
after the route was live.

A longer sleep would still be a guess; this polls for the real condition.
"""

from __future__ import annotations

import time

import httpx

_POLL_INTERVAL_SEC = 0.2
_PROBE_TIMEOUT_SEC = 3.0

_PROBE_BODY = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-11-25",
        "capabilities": {},
        "clientInfo": {"name": "self-probe", "version": "0.1"},
    },
}
_PROBE_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def wait_until_serving(port: int, timeout_sec: float = 30.0) -> bool:
    """Poll `http://127.0.0.1:<port>/mcp` until it stops answering 404.

    Returns True once the route responds with anything other than 404 (a 200,
    or a protocol-level rejection -- both prove the route is mounted), False if
    `timeout_sec` elapses first. Connection errors are treated as "not up yet".
    """
    url = f"http://127.0.0.1:{port}/mcp"
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            response = httpx.post(
                url, json=_PROBE_BODY, headers=_PROBE_HEADERS, timeout=_PROBE_TIMEOUT_SEC
            )
        except Exception:  # noqa: BLE001 - socket not accepting yet; keep polling
            time.sleep(_POLL_INTERVAL_SEC)
            continue
        if response.status_code != 404:
            return True
        time.sleep(_POLL_INTERVAL_SEC)
    return False
