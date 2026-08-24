# bb-ai-12 — Police Peer

Final project for the "AI Agent Orchestration" course (Dr. Yoram Segal): a fully
decentralized, peer-to-peer AI agent that plays the **police** role against an
independently-developed **thief** agent, with no central server, no shared memory, and no
referee. Binding specification: `police_thief_p2p.pdf` v3.0.0 — where anything here
conflicts with the book, the book wins.

**Sibling repo (thief side):** https://github.com/BoshraDh/ai_agents_final_project_thief

**Team code:** `bb-ai-12`

## Status
✅ **All 7 build stages complete, plus the real turn-taking protocol and automatic
end-of-game detection** (base logic + MCP infra + blind strategy + language/scent + cloud
tunneling + security + reporting shell + real Commit→Acknowledge→Reveal turn protocol +
automatic capture/survival stop). See `docs/PLAN.md` for what was built at each stage and
`docs/TODO.md` for the deferred integration work still open before a real submission-counted
match.

✅ **Round-1 commit-reveal race fixed**: two freshly-started, independent peer processes
previously failed on round 1 due to a missing synchronization point in the wire protocol; an
inbound reveal now waits for this peer's own reveal to be locally ready instead of failing
immediately. Re-verified with a real 40-turn two-process run — see `docs/TODO.md`.

✅ **Benign teardown race also fixed**: whichever side reached `GAME OVER` first used to exit
immediately, occasionally cutting off the opponent's still-in-flight final-round call. `peer`
now waits a few seconds after the outcome leaves `ONGOING` before exiting. Re-verified live:
both processes now exit cleanly (code 0, zero errors) — see `docs/TODO.md`.

⚠️ **2026-08-24 — one deliberate exception to "the book wins"**: the commit-reveal hash formula
now follows the league's shared `copthief-league-protocol` kit instead of the book's ch.5.3
literal formula, after live negotiation confirmed the real opponent pool runs the kit's
version. A conscious, explicitly-flagged trade-off (interoperability over strict spec
compliance) — see the "Open flag" in `docs/TODO.md` before final submission.

✅ **New: league kit 4-tool protocol adapter** (`bb-ai-12-police league-peer`) — plays real
matches against opponents that run the `copthief-league-protocol` kit's wire shape
(`negotiate`/`receive_turn`/`submit_audit`/`receive_control`) instead of this repo's own
`submit_commit`/`submit_reveal`. Verified end-to-end with a real two-sided smoke test — see
`docs/PRD_league_adapter.md`.

✅ **New: automatic end-of-game report email** — `report/emit.py` now builds the four mandatory
JSON artifacts, writes them, and emails them to the grader (`config/game.toml`'s
`[email].recipient`) via the already-live-verified Gmail OAuth setup, automatically whenever
`peer`/`league-peer` finish with a real outcome. No more manual step. See `docs/TODO.md`'s
"Done (automatic send-report hook)".

No known blockers remain for a real live match at this point.

## Quick start (localhost — development and smoke testing)

```bash
uv sync
uv run pytest -q --cov=src --cov-report=term-missing   # 162 tests, 90% coverage
uv run ruff check .                                      # zero violations
uv run bb-ai-12-police check-config                       # sanity-check config loading
uv run bb-ai-12-police declare                            # print a sealed Step-0 declaration
uv run bb-ai-12-police replay --log logs/bb-ai-12/log_*.json   # step through a saved log
```

Two-terminal round-trip smoke test (run the thief repo's equivalent command first in its own
terminal, then this one). Both peers now play real, genuinely bidirectional rounds: each side
commits (SHA-256 hash), then reveals its own real strategy-chosen move + trash-talk hint, and
receives the *opponent's* real reveal back in the same round trip (see
`docs/PRD_turn_protocol.md`):

```bash
uv run bb-ai-12-police peer --turns 3
```

## Real match (public tunnel — a different environment from localhost)

To let an opponent team on another machine reach this peer, install
[ngrok](https://ngrok.com/download) and run `ngrok config add-authtoken <token>` once (from
your free ngrok dashboard), then:

```bash
uv run bb-ai-12-police tunnel
```

This prints a public `https://.../mcp` URL — send it to your opponent team as their
`opponent_url`. **Not run automatically by anything in this repo or its tests** — opening a
public port is a live action only the person running a real match should trigger; see
`docs/PRD_cloud_tunnel.md` for why.

## Architecture
See `docs/PLAN.md` for the full target architecture diagram and the 7-stage build order
(book §10.3). In short: `SimulationSdk` → `PeerRuntime` (negotiate → turn loop → audit) →
`domain` (board/barriers/rules/scoring/pheromones/belief) + `strategy` (pure-Python brain,
LLM never picks the move) + `crypto` (commit-reveal) + `report` (the 4 mandatory JSON
artifacts) + `infra`/`shared` (MCP transport, config, rate limiting).

## Documentation
- `docs/PRD.md` — functional & non-functional requirements.
- `docs/PLAN.md` — architecture and build-stage plan.
- `docs/TODO.md` — live task list, updated every change.
- `docs/PRD_base_logic.md` / `docs/PRD_mcp_infra.md` / `docs/PRD_strategy.md` /
  `docs/PRD_language_scent.md` / `docs/PRD_cloud_tunnel.md` / `docs/PRD_security_crypto.md` /
  `docs/PRD_reporting_shell.md` / `docs/PRD_turn_protocol.md` /
  `docs/PRD_end_of_game_detection.md` — per-stage detail (all 7 stages plus the real
  turn-taking protocol and automatic end-of-game detection).

## Academic report
The full 6-section academic report (rules model, communication approach, decision-making,
LLM usage, live-GUI verification, replay-viewer verification) is not yet written up here —
all the underlying code it would describe (strategy, pheromones, commit-reveal, the live GUI,
the replay viewer) now exists and is tested, per `docs/PLAN.md`. Writing the report itself is
still open, tracked in `docs/TODO.md`.

## Reference & attribution
Structural patterns (module layout, `game.json`/`game.toml` split, `SimulationSdk`/
`PeerRuntime` naming) are adapted from the course's public reference simulator
(https://github.com/rmisegal/Game-P2P-Cop-Chase), per its own stated terms and the
instructor's explicit permission to reuse parts of it. No code was copied verbatim; the
strategy and full implementation here are original. See `LICENSE`.

## License
Educational use — see `LICENSE`.
