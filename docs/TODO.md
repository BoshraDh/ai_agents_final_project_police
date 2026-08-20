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

## Done (Stage 3 — Blind strategy)
- [x] `domain/belief.py` — `BeliefState`, exact position tracker from honestly-relayed moves.
- [x] `strategy/base.py` — `BrainBase` contract (`decide_move`).
- [x] `strategy/heuristic_brain.py` — Manhattan-distance search over `domain.rules.legal_moves`
      (default, zero LLM tokens).
- [x] `strategy/police_brain.py` — pursuit subclass (`_sign=1`).
- [x] `strategy/resolve_brain.py` — factory reading `[strategy]` from `config/game.toml`;
      `game.toml`'s `[strategy]` section is now uncommented and live.
- [x] Replaced `PeerRuntime._decide_move`'s hardcoded STAY with the resolved brain's output.
- [x] Manual test: ran this repo + the thief repo concurrently — real strategy confirmed
      driving outbound moves on both sides (see `docs/PRD_strategy.md`).
- [x] 46 tests, 94% coverage, ruff-clean.
- [x] Updated this file, PLAN.md, PRD.md, PRD_strategy.md, README.md.

## Done (Stage 4 — Language + scent)
- [x] `domain/pheromones.py` — `PheromoneField`, single-cell τij(t+1)=max(0,(1-ρ)τij(t)+Δτij).
- [x] `llm/provider_base.py` + `llm/template_provider.py` (default, 0 tokens) — trash-talk text
      generation only; the move is still never chosen by the LLM.
- [x] `llm/resolve_provider.py` — factory reading `[trash_talk]` from `config/game.toml`.
- [x] Extended the wire message shape (`direction`+`turn`) to also carry a `hint` field capped
      at `hint_max_words`, honestly relayed for now.
- [x] `runtime/peer_runtime.py` steps an `opponent_scent` `PheromoneField` from the tracked
      opponent position each turn (see `docs/PRD_language_scent.md` for why this is currently
      redundant with `BeliefState`, and what makes it load-bearing later).
- [x] Manual test: ran this repo + the thief repo concurrently — real, distinct hint text
      confirmed flowing on outbound turns on both sides (see `docs/PRD_language_scent.md`).
- [x] 57 tests, 95% coverage, ruff-clean.
- [x] Updated this file, PLAN.md, PRD.md, PRD_language_scent.md, README.md.

## Next (Stage 5 — Cloud exposure + tunneling)
- [ ] Pick and document a tunneling tool (ngrok or Localtonet) for exposing `my_port`
      publicly so a real opponent team (not just localhost) can reach this peer.
- [ ] `mcp/tunnel.py` — thin wrapper that starts/stops the tunnel and reports the public URL.
- [ ] Document the environment separation between "localhost smoke test" (current `peer`
      subcommand) and "real match over a public tunnel" in README.md.
- [ ] Update `config/game.toml`'s `opponent_url` handling to accept a tunnel URL, not just
      `127.0.0.1`.
- [ ] Update this file, PLAN.md, PRD.md again once stage 5 is committed.

## Open flags (not blocking, must resolve before a real submission-counted match)
- [ ] **`num_games`** — confirm against the book text whether the mandated per-series value
      is `6` (as the reference repo's README claims) or the Appendix ו example `1`; update
      `config/game.json` in both repos together if it changes.
- [ ] Replace `agreed_between: ["bb-ai-12", "<opponent-team-code>"]` with the real opponent
      code once a match is negotiated (both repos, kept byte-identical).
- [ ] Replace `[game].members` placeholder student IDs in `config/game.toml`.
- [ ] **Synchronized turn-taking / negotiation handshake** — `mcp/server.py`'s inbound
      `receive_move` still always echoes STAY (unchanged since stage 2); only this peer's
      outbound moves use the real brain. Making the inbound side reply with a real move needs
      a proper `peer/turn_handler.py` + `peer/handshake.py` + `domain/negotiation.py` protocol,
      deliberately not improvised in stage 3 — see `docs/PRD_strategy.md`'s design-decision
      note. Build alongside stage 5/6's cloud + security work, re-checking the book's
      negotiation-protocol text first.
- [ ] **Barrier placement** — `PoliceBrain` only ever chooses a movement direction; it doesn't
      yet decide when/where to place a barrier, and the wire protocol doesn't carry barrier
      messages. Add once the message schema is extended (likely alongside the stage above).
- [ ] **Pheromone spatial spread** — re-confirm the book's exact spatial falloff shape for
      `pheromone_grid_size` (uniform vs. weighted neighborhood deposit) before implementing
      anything beyond the current single-cell deposit in `domain/pheromones.py`.

## Later stages (tracked here for visibility, detailed in their own PRD_*.md once started)
- [ ] Stage 5 — Cloud exposure + tunneling (ngrok/Localtonet).
- [ ] Stage 6 — Security (commit-reveal, nonce, Step-0 declaration, SHA-256 handshake).
- [ ] Stage 7 — Reporting shell (Gmail OAuth2, Gatekeeper, Live GUI, Replay Viewer).
- [ ] At least 2 full games played against a real opponent team before submission
      (`min_games_to_pass = 2`).
- [ ] `git tag -a v1.0-submission` once feature-complete.
