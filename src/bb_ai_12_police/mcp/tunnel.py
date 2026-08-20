"""ngrok tunnel wrapper: exposes this peer's MCP port to the public internet.

Stage 5: publishes `mcp/server.py`'s port through a local `ngrok http <port>`
process, so a real opponent team (not just localhost) can reach this peer.
Requires the `ngrok` binary installed and authenticated
(`ngrok config add-authtoken ...`) — see `docs/PRD_cloud_tunnel.md` for the
one-time setup steps, deliberately not run automatically by this class or
by any test in this repo: starting a public tunnel is a live
network-exposure action, taken only when actually playing a match.
"""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from typing import Any

import httpx

_NGROK_LOCAL_API = "http://127.0.0.1:4040/api/tunnels"


def _default_fetch_json(url: str) -> dict[str, Any]:
    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json()


class NgrokTunnel:
    """Starts/stops a local `ngrok http <port>` process; reports its public URL."""

    def __init__(
        self,
        port: int,
        api_url: str = _NGROK_LOCAL_API,
        launch: Callable[[list[str]], subprocess.Popen] = subprocess.Popen,
        fetch_json: Callable[[str], dict[str, Any]] = _default_fetch_json,
    ) -> None:
        self.port = port
        self.api_url = api_url
        self._launch = launch
        self._fetch_json = fetch_json
        self._process: subprocess.Popen | None = None

    def start(self, startup_delay_sec: float = 2.0) -> str:
        """Launch `ngrok http <port>`; return its public `https://` URL."""
        self._process = self._launch(["ngrok", "http", str(self.port)])
        time.sleep(startup_delay_sec)
        payload = self._fetch_json(self.api_url)
        for tunnel in payload["tunnels"]:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
        raise RuntimeError("ngrok is running but reported no https tunnel")

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()
            self._process = None
