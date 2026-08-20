# PLAN — bb-ai-12 Police Peer

## Source of truth
Game rules/binding parameters: `police_thief_p2p.pdf` v3.0.0 (book), Appendix ו for all
numeric values. Where this repo differs from the book, the book wins. Submission process
rules: `software_submission_guidelines-V3.pdf` (V3.00).

## Architecture (target, built incrementally — see Build Stages below)

```
CLI (cli.py)
   |
SimulationSdk (sdk/) -- run_peer: N-sub-game series loop
   |
PeerRuntime (runtime/) -- negotiate -> turn loop -> audit
   |-- state_machine.py   GamePhaseMachine, explicit legal-transition table
   |-- deadline_tracker.py / watchdog.py   reliability
   |
mcp/        FastMCP server (receive_move tool) + client (McpTransport) + tunnel
domain/     board, barriers, rules, scoring, protocol, pheromones, belief, negotiation
peer/       turn_handler, sealing, handshake, summary
crypto/     commit_reveal (SHA-256), step0 (hardware declaration)
strategy/   base (BrainBase), heuristic_brain (default), police_brain, resolve_brain factory
llm/        provider_base, template (default), ollama, claude_api, claude_cli
report/     artifacts (4 JSON builders), emit, report_writer
infra/      email_sender (Gmail OAuth2)
shared/     config_manager (game.json+game.toml), api_gatekeeper, sysinfo, version
gui/        live_gui (local-truth heatmap), replay_viewer (SHA-256 re-verify)
```

Sibling repo: `bb-ai-12-thief` (https://github.com/BoshraDh/ai_agents_final_project_thief) —
structurally identical skeleton, opposite role's brain, mirrored ports (thief=8801,
police=8802). `config/game.json` in both repos must stay byte-identical (verified via
SHA-256 in the pre-game handshake, stage 6).

## Stage 1 — what was built
- `domain/protocol.py` — `Role`, `Direction`, `Position`, `GameOutcome`, `MoveAction` (shared
  value types, stdlib-only).
- `domain/board.py` — `Board`: bounds checking, legal directions, start-position lookup.
- `domain/barriers.py` — `BarrierSet`: police-only placement adjacent to self, capped at
  `max_barriers`, irrevocable.
- `domain/rules.py` — `is_legal_move`, `resolve_capture_claim`, `check_survival`,
  `outcome_after_step` (single source of truth for "is the sub-game over").
- `domain/scoring.py` — fixed score table from Appendix ו (20/5/5/10/2/0), never edited.
- `shared/config_manager.py` — loads `config/game.json` (shared, signed) + `config/game.toml`
  (private), exposes `game_json_sha256()` for the future pre-game handshake.
- `config/game.json` + `config/game.toml` — populated with the book's binding defaults.
- `cli.py` — minimal `check-config` subcommand only; `peer`/`replay` subcommands arrive in
  stages 2 and 7.

No networking, no crypto, no LLM yet — deliberately, per the book's own warning against
skipping layers.

## Stage 2 — what was built
- `mcp/server.py` — `FastMCP(name="bb-ai-12-police")` with a `receive_move` tool; stage-2 stub
  always replies STAY. `run_server(host, port)` serves streamable HTTP at `/mcp`.
- `mcp/client.py` — `McpTransport` wraps `fastmcp.Client`; `send_move`/`send_move_async` call
  the opponent's `receive_move` tool.
- `runtime/peer_runtime.py` — `PeerRuntime`: starts the server in a background thread, then
  `run_turn_loop(turns)` sends hardcoded STAY moves and prints each reply.
- `cli.py peer --turns N` — manual smoke-test subcommand.
- **Manually verified real round trip** between this repo and the thief repo, each running as
  its own process on localhost (ports 8802/8801) — see `docs/PRD_mcp_infra.md` for the exact
  transcript and the known benign teardown-race caveat (fixed properly once the real
  synchronized turn-taking protocol lands — see the Stage 3 note below — not patched here).

Still no strategy (hardcoded STAY), no crypto, no LLM — per the book's layering order.

## Stage 3 — what was built
- `domain/belief.py` — `BeliefState`: exact position tracker, replayed from public start
  positions + honestly-relayed moves (deterministic until stage 4's deception/stage 6's
  crypto make it genuinely uncertain).
- `strategy/base.py` — `BrainBase` abstract contract (`decide_move`); LLM never decides.
- `strategy/heuristic_brain.py` — `HeuristicBrain` + `manhattan()`: Manhattan-distance search
  over `domain.rules.legal_moves`, `_sign` toggles pursue vs evade.
- `strategy/police_brain.py` — `PoliceBrain(HeuristicBrain)`, `_sign=1` (chases the thief).
- `strategy/resolve_brain.py` — factory reading `[strategy].police_class` from
  `config/game.toml`, defaulting to `PoliceBrain`; `game.toml`'s `[strategy]` is now live.
- `runtime/peer_runtime.py` — `_decide_move` calls the resolved brain; `run_turn_loop` updates
  `BeliefState` on both the move sent and the move received.
- **Manually verified with real strategy on both sides**: this repo's outbound moves are now
  genuine pursuit decisions, not hardcoded STAY — see `docs/PRD_strategy.md` for the exact
  transcript. `mcp/server.py`'s inbound stub deliberately stays STAY-only for now (see the
  design-decision note in `docs/PRD_strategy.md` on why synchronized turn-taking is deferred,
  not built ad hoc, to a later stage rather than guessed at here).

Still no barrier-placement decisions, no scent/hints, no crypto, no LLM — per the book's
layering order.

## Stage 4 — what was built
- `domain/pheromones.py` — `PheromoneField`: τij(t+1)=max(0,(1-ρ)τij(t)+Δτij), single-cell
  deposit+decay (spatial spread across `pheromone_grid_size` not yet implemented — needs
  book re-confirmation of the falloff shape first).
- `llm/provider_base.py` — `TrashTalkProvider`: abstract `_generate(turn)`, concrete
  `hint(turn)` enforces `hint_max_words`.
- `llm/template_provider.py` — `TemplateProvider`: 0-token canned sentence bank, the required
  zero-LLM default (NFR-8).
- `llm/resolve_provider.py` — factory reading `[trash_talk].provider`; only `template` is
  implemented, others raise `NotImplementedError`.
- `mcp/server.py` / `mcp/client.py` — `receive_move`/`send_move` gain a `hint` field.
- `runtime/peer_runtime.py` — `run_turn_loop` sends a real hint each turn and steps
  `opponent_scent` (a `PheromoneField`) from the tracked opponent position.
- **Manually verified with real hints on both sides** — see `docs/PRD_language_scent.md` for
  the exact transcript and the design decisions on why `opponent_scent` is currently
  redundant with `BeliefState`, and why deceptive hints wait on stage 6's crypto audit.

Still no barrier-placement decisions, no crypto, no real LLM providers — per the book's
layering order.

## Build stages (book's own priority order — each runs end-to-end before the next starts)
1. Base logic — grid, movement, barriers, capture, scoring. No networking. *(done)*
2. MCP infra — FastMCP server/client on localhost, no strategy yet. *(done)*
3. Blind strategy — heuristic move-decision (Manhattan distance), still no language/scent.
   *(done)*
4. Language + scent — pheromone math, free-text hints, LLM plugged in for banter text only.
   *(done)*
5. Cloud exposure + tunneling — ngrok, environment separation. *(done)*
6. **Security** — Commit-Reveal, Nonce, Step-0 hardware declaration, pre-game SHA-256
   handshake. *(current)*
7. Reporting shell — Gmail OAuth2 + Gatekeeper, Live GUI, Replay Viewer.

## Stage 5 — what was built
- `mcp/tunnel.py` — `NgrokTunnel`: wraps a local `ngrok http <port>` process, `start()`
  returns the public `https://` URL read from ngrok's local API, `stop()` terminates it.
  Fully unit-testable via injected `launch`/`fetch_json` callables — no real process or
  network call in the test suite.
- `cli.py tunnel` — new subcommand: starts the tunnel, prints the public MCP URL to hand to
  an opponent team, blocks until Ctrl+C.
- **Deliberately not run live this session** — see `docs/PRD_cloud_tunnel.md`'s design
  decision: exposing a real public port needs installing `ngrok` and creating an account, so
  per an explicit check-in with the user, that step is hers to run when actually ready for a
  match (same "walk me through it live" pattern already agreed for stage 7's Gmail OAuth).

Still no barrier-placement decisions, no crypto, no real LLM providers, no live public
exposure yet — per the book's layering order and the design decision above.

## Open items / flags (tracked, not silently decided)
- **`num_games` figure**: the reference repo's README states "the guidelines book mandates
  6" for `network_and_league.num_games` (sub-games per series against one opponent, with
  role-alternation). Our `config/game.json` currently ships the book Appendix ו's own
  example value of `1`. This is a mutual, per-match setting — re-confirm the real mandated
  value against the book text before the first real submission-counted match, and update
  both repos' `config/game.json` together if it changes. See `docs/TODO.md`.
- `agreed_between` in `config/game.json` currently lists `"<opponent-team-code>"` as a
  placeholder — fill in the real opponent code once a match is negotiated, in both repos.
- `config/game.toml` `[game].members` lists placeholder student IDs — fill in real IDs.
