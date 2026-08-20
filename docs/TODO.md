# TODO — bb-ai-12 Police Peer

## Done
- [x] Repo scaffolding (`uv init --package`), pyproject.toml (v1.0.0, ruff+pytest config).
- [x] `config/game.json` (shared, binding defaults from Appendix ו) + `config/game.toml`
      (private, ports/team/LLM settings).
- [x] Stage 1 — Base logic: board, barriers, rules, scoring, config loading. 31 tests,
      97% coverage, ruff-clean.
- [x] `docs/PRD.md`, `docs/PLAN.md`, `docs/PRD_base_logic.md`, this file.
- [x] `.gitignore`, `.env-example`, `LICENSE`, `README.md` skeleton.

## Done (Stage 2 — MCP infra)
- [x] Added `fastmcp`+`httpx` dependencies (`uv add fastmcp httpx`).
- [x] `mcp/server.py` — FastMCP server exposing a `receive_move` tool on `my_port` (8802).
- [x] `mcp/client.py` (`McpTransport`) — calls the opponent's `opponent_url`.
- [x] `runtime/peer_runtime.py` — turn loop skeleton (hardcoded always-STAY move).
- [x] `cli.py peer --turns N` subcommand for manual smoke testing.
- [x] Manual test: ran this repo + the thief repo concurrently on localhost — real
      bidirectional round trip confirmed (see `docs/PRD_mcp_infra.md` for the exact result).
- [x] 37 tests, 93% coverage, ruff-clean.
- [x] Updated this file, PLAN.md, PRD.md, PRD_mcp_infra.md, README.md.

## Next (Stage 3 — Blind strategy)
- [ ] `strategy/base.py` — `BrainBase` contract (`decide_move`).
- [ ] `strategy/heuristic_brain.py` — Manhattan distance + Bayesian belief over the opponent's
      last-known/inferred position (default, zero LLM tokens).
- [ ] `strategy/police_brain.py` — police-specific subclass (barrier-aware pursuit).
- [ ] `strategy/resolve_brain.py` — factory reading `[strategy]` from `config/game.toml`.
- [ ] Replace `PeerRuntime._decide_move`'s hardcoded STAY with the resolved brain's output.
- [ ] Real synchronized turn-taking (negotiation handshake) to replace the ad-hoc two-script
      smoke test from stage 2.
- [ ] Update this file, PLAN.md, PRD.md again once stage 3 is committed.

## Open flags (not blocking, must resolve before a real submission-counted match)
- [ ] **`num_games`** — confirm against the book text whether the mandated per-series value
      is `6` (as the reference repo's README claims) or the Appendix ו example `1`; update
      `config/game.json` in both repos together if it changes.
- [ ] Replace `agreed_between: ["bb-ai-12", "<opponent-team-code>"]` with the real opponent
      code once a match is negotiated (both repos, kept byte-identical).
- [ ] Replace `[game].members` placeholder student IDs in `config/game.toml`.
- [ ] Decide `police_class` in `[strategy]` once stage 3's `PoliceBrain` exists (currently
      commented out — default heuristic runs unset).

## Later stages (tracked here for visibility, detailed in their own PRD_*.md once started)
- [ ] Stage 3 — Blind strategy (heuristic brain: Manhattan distance + Bayesian belief).
- [ ] Stage 4 — Language + scent (pheromone math, free-text hints, template LLM banter).
- [ ] Stage 5 — Cloud exposure + tunneling (ngrok/Localtonet).
- [ ] Stage 6 — Security (commit-reveal, nonce, Step-0 declaration, SHA-256 handshake).
- [ ] Stage 7 — Reporting shell (Gmail OAuth2, Gatekeeper, Live GUI, Replay Viewer).
- [ ] At least 2 full games played against a real opponent team before submission
      (`min_games_to_pass = 2`).
- [ ] `git tag -a v1.0-submission` once feature-complete.
