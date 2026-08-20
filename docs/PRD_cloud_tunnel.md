# PRD — Stage 5: Cloud Exposure + Tunneling

## Goal
Let a real opponent team's peer (running on a different machine, not localhost) reach this
peer's MCP server. The book's own environment-separation warning applies: a public tunnel is
a genuinely different environment from the `peer --turns N` localhost smoke test used in
stages 2-4, so it gets its own stage rather than being folded into an existing one.

## Delivered
| Module | Responsibility |
|---|---|
| `mcp/tunnel.py` | `NgrokTunnel` — wraps a local `ngrok http <port>` process; `start()` launches it and returns the public `https://` URL (read from ngrok's local API at `127.0.0.1:4040`); `stop()` terminates the process |
| `cli.py` | new `tunnel` subcommand — starts the tunnel, prints the public MCP URL to hand to an opponent team as their `opponent_url`, blocks until Ctrl+C |

## Design decision: no live tunnel run in this session
Starting a real `ngrok` tunnel means (a) installing a third-party binary, (b) creating an
ngrok account and authtoken for anything beyond the most limited anonymous tier, and
(c) actually opening this machine's port to the public internet — a materially different
risk category from anything built in stages 1-4, all of which stayed on localhost. Per an
explicit check-in with the user this session, this class and CLI command are built, unit
tested (via injected fakes — no real process spawned, no real HTTP call made), and
documented, but **not run live**. The user runs `bb-ai-12-police tunnel` herself when actually
ready to expose this peer for a real match; this mirrors the same "walk me through it live"
approach already agreed for the stage-7 Gmail OAuth setup, applied here because the two
actions share the same risk shape (installing a tool + granting real-world access).

## One-time setup (for the user, when ready to run a live match)
1. Install `ngrok` (https://ngrok.com/download) and create a free account.
2. `ngrok config add-authtoken <your-token>` (from the ngrok dashboard) — one-time, stores
   the token in ngrok's own config, never committed to this repo.
3. `uv run bb-ai-12-police tunnel` — starts this peer's MCP server is *not* started by this
   command; run `uv run bb-ai-12-police peer` (or the eventual real match command) in another
   terminal alongside it, or extend `_run_tunnel` later to also start the server. Prints the
   public `https://<random>.ngrok-free.app/mcp` URL — send this to the opponent team as the
   `opponent_url` they should put in their own `config/game.toml`.
4. Ctrl+C stops the tunnel cleanly.

## Acceptance criteria (all met)
- [x] `NgrokTunnel.start` launches `["ngrok", "http", str(port)]` via an injectable `launch`
      callable and reads the public HTTPS URL from an injectable `fetch_json` callable —
      fully testable without a real process or network call.
- [x] Raises `RuntimeError` with a clear message if ngrok is running but reports no `https`
      tunnel (e.g., only an `http` one, or none yet).
- [x] `stop()` terminates the tracked process; a no-op if never started.
- [x] `uv run pytest -q --cov=src` passes at 92% coverage (61 tests, `cli.py`'s `_run_tunnel`
      itself uninstrumented like `_run_peer` before it — both require real external
      interaction and are exercised manually, not in the unit-test suite); `uv run ruff
      check .` is clean.

## Explicitly deferred to later stages
- Actually running a live tunnel — the user's own action, on match day, per the design
  decision above.
- `opponent_url` in `config/game.toml` still points at `127.0.0.1` for local smoke testing;
  swapping it for a real tunnel URL is a manual, per-match edit (not automated), consistent
  with `config/game.json`'s existing "manual, documented step" pattern from `docs/PLAN.md`.
- Barrier placement, synchronized turn-taking, deceptive hints — still open from earlier
  stages (see `docs/TODO.md`).
- Commit-reveal sealing, nonces, Step-0 declaration, real negotiation handshake — stage 6.
- Gmail reporting, GUI, replay viewer — stage 7.
