"""`tunnel` — expose my_port publicly via ngrok, print the URL."""

from __future__ import annotations

import time

from bb_ai_12_police.mcp.tunnel import NgrokTunnel
from bb_ai_12_police.shared.config_manager import ConfigManager


def run(repo_root: str) -> int:
    """Requires the `ngrok` binary installed + authenticated; blocks until Ctrl+C."""
    net = ConfigManager(repo_root).load_private()["network"]
    tunnel = NgrokTunnel(port=net["my_port"])
    public_url = tunnel.start()
    print(f"Public MCP URL: {public_url}/mcp")
    print("Share this with your opponent team as their `opponent_url`. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        tunnel.stop()
    return 0
