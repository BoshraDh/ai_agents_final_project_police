# bb-ai-12 — Police Peer

Final project for the "AI Agent Orchestration" course (Dr. Yoram Segal): a fully
decentralized, peer-to-peer AI agent that plays the **police** role against an
independently-developed **thief** agent, with no central server, no shared memory, and no
referee. Binding specification: `police_thief_p2p.pdf` v3.0.0 — where anything here
conflicts with the book, the book wins.

**Sibling repo (thief side):** https://github.com/BoshraDh/ai_agents_final_project_thief

**Team code:** `bb-ai-12`

## Status
🚧 **Stage 5 of 7 complete** (base logic + MCP infra + blind strategy + language/scent +
cloud tunneling). See `docs/PLAN.md` for the full build-stage roadmap and `docs/TODO.md` for
exactly what's next.

## Quick start (localhost — development and smoke testing)

```bash
uv sync
uv run pytest -q --cov=src --cov-report=term-missing   # 61 tests, 92% coverage
uv run ruff check .                                      # zero violations
uv run bb-ai-12-police check-config                       # sanity-check config loading
```

Two-terminal round-trip smoke test (run the thief repo's equivalent command first in its own
terminal, then this one). This peer's outbound moves are now real Manhattan-distance pursuit
decisions with a real trash-talk hint attached each turn; the inbound reply is still a
stage-2 STAY stub with a placeholder hint until the synchronized turn-taking protocol lands
(see `docs/PRD_strategy.md`):

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
  `docs/PRD_language_scent.md` / `docs/PRD_cloud_tunnel.md` — per-stage detail (stages 1-5).

## Academic report
The full 6-section academic report (rules model, communication approach, decision-making,
LLM usage, live-GUI verification, replay-viewer verification) will be added to this README
once the corresponding stages (GUI/replay, stage 7) are implemented, per the submission
guidelines.

## Reference & attribution
Structural patterns (module layout, `game.json`/`game.toml` split, `SimulationSdk`/
`PeerRuntime` naming) are adapted from the course's public reference simulator
(https://github.com/rmisegal/Game-P2P-Cop-Chase), per its own stated terms and the
instructor's explicit permission to reuse parts of it. No code was copied verbatim; the
strategy and full implementation here are original. See `LICENSE`.

## License
Educational use — see `LICENSE`.
