"""Tests for the ngrok tunnel wrapper — no real process or network call.

`launch`/`fetch_json` are injected fakes throughout, so these tests never
spawn a real `ngrok` process or hit its local API.
"""

from __future__ import annotations

import pytest

from bb_ai_12_police.mcp.tunnel import NgrokTunnel


class _FakeProcess:
    def __init__(self) -> None:
        self.terminated = False

    def terminate(self) -> None:
        self.terminated = True


def test_start_launches_ngrok_and_returns_the_https_public_url():
    launched_args = []

    def fake_launch(args):
        launched_args.append(args)
        return _FakeProcess()

    def fake_fetch_json(url):
        return {
            "tunnels": [
                {"proto": "http", "public_url": "http://abc123.ngrok.io"},
                {"proto": "https", "public_url": "https://abc123.ngrok.io"},
            ]
        }

    tunnel = NgrokTunnel(port=8802, launch=fake_launch, fetch_json=fake_fetch_json)
    public_url = tunnel.start(startup_delay_sec=0)

    assert public_url == "https://abc123.ngrok.io"
    assert launched_args == [["ngrok", "http", "8802"]]


def test_start_raises_when_no_https_tunnel_is_reported():
    tunnel = NgrokTunnel(
        port=8802,
        launch=lambda args: _FakeProcess(),
        fetch_json=lambda url: {"tunnels": [{"proto": "http", "public_url": "x"}]},
    )
    with pytest.raises(RuntimeError):
        tunnel.start(startup_delay_sec=0)


def test_stop_terminates_the_launched_process():
    process = _FakeProcess()
    tunnel = NgrokTunnel(
        port=8802,
        launch=lambda args: process,
        fetch_json=lambda url: {"tunnels": [{"proto": "https", "public_url": "https://x"}]},
    )
    tunnel.start(startup_delay_sec=0)
    tunnel.stop()
    assert process.terminated


def test_stop_is_a_no_op_if_never_started():
    tunnel = NgrokTunnel(port=8802, launch=lambda args: _FakeProcess(), fetch_json=lambda url: {})
    tunnel.stop()
