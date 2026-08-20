# bb-ai-12 — Police Peer

Final project for the "AI Agent Orchestration" course (Dr. Yoram Segal): a fully
decentralized, peer-to-peer AI agent that plays the **police** role against an
independently-developed **thief** agent, with no central server, no shared memory, and no
referee. Binding specification: `police_thief_p2p.pdf` v3.0.0 — where anything here
conflicts with the book, the book wins.

**Sibling repo (thief side):** https://github.com/BoshraDh/ai_agents_final_project_thief

**Team code:** `bb-ai-12`

## Status
🚧 **Stage 1 of 7 complete** (base logic). See `docs/PLAN.md` for the full build-stage
roadmap and `docs/TODO.md` for exactly what's next.

## Quick start (current stage — no networking yet)

```bash
uv sync
uv run pytest -q --cov=src --cov-report=term-missing   # 31 tests, 97% coverage
uv run ruff check .                                      # zero violations
uv run python -m bb_ai_12_police check-config             # sanity-check config loading
```

Once stage 2 (MCP networking) lands, this section will be replaced with the real two-terminal
`peer --role police` / `peer --role thief` instructions, matching the reference simulator's
operational pattern.

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
- `docs/PRD_base_logic.md` — stage-specific detail for the current stage.

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
