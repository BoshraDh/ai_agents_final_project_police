# PRD — Stage 2: MCP Infra

## Goal
Prove the P2P wire works end-to-end: this peer is simultaneously a FastMCP server (inbound)
and a FastMCP client (outbound) talking to the sibling thief peer over real HTTP sockets, on
localhost, with no strategy, crypto, or scoring involved yet — every move sent is a hardcoded
`STAY`.

## Delivered
| Module | Responsibility | Book reference |
|---|---|---|
| `mcp/server.py` | `FastMCP` instance; `receive_move` tool (stub reply: STAY); `run_server(host, port)` blocks serving streamable HTTP at `/mcp` | ch.5 (communication layer) |
| `mcp/client.py` | `McpTransport` — wraps `fastmcp.Client`, `send_move`/`send_move_async` call the opponent's `receive_move` tool | ch.5 |
| `runtime/peer_runtime.py` | `PeerRuntime` — starts the server in a background thread, then runs `run_turn_loop(turns)` sending hardcoded STAY moves out | ch.5, ch.7 (turn loop) |
| `cli.py` | new `peer --turns N` subcommand — manual round-trip smoke test | — |

## Acceptance criteria (all met)
- [x] `receive_move(direction, turn)` always replies `{"direction": "STAY", "turn": turn}` —
      verified by unit test against the raw function and, separately, against an in-process
      `fastmcp.Client` (no real socket).
- [x] `McpTransport.send_move` round-trips against the in-process server in tests.
- [x] `PeerRuntime.run_turn_loop` sends exactly `turns` moves, verified with a monkeypatched
      transport (no real networking in the unit-test suite).
- [x] **Real two-process round trip, manually verified**: ran `bb-ai-12-thief peer --turns 3`
      and `bb-ai-12-police peer --turns 3` concurrently, each in its own repo, over actual
      `127.0.0.1:8801`/`127.0.0.1:8802` HTTP sockets. Turns 1-2 completed a full bidirectional
      round trip on both sides (each peer's outbound call reached the other's `receive_move`
      and got the STAY reply back; each peer's inbound handler logged the opponent's move).
      Turn 3 hit a benign `httpx.ReadError` on the police side because the two one-shot
      3-turn scripts aren't synchronized — the thief process finished its loop and began
      tearing down its server right as police's 3rd call arrived. This is expected for this
      stage's stub scripts (no real turn-taking protocol yet) and is not a defect to fix here;
      stage 3's real turn loop replaces this ad-hoc script with a synchronized protocol.
- [x] `uv run pytest -q --cov=src` passes at 93% coverage; `uv run ruff check .` is clean.

## Explicitly deferred to later stages
- Any actual move decision (still hardcoded STAY) — stage 3.
- Synchronized turn-taking / negotiation handshake — stage 3.
- Pheromones/belief/hints — stage 4.
- Cloud tunneling (ngrok/Localtonet) — stage 5.
- Commit-reveal sealing, nonces, Step-0 declaration — stage 6.
- Gmail reporting, GUI, replay viewer — stage 7.
