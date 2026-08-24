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

## Stage 6 — what was built
- `crypto/commit_reveal.py` — `canonical_json`, `generate_nonce` (`secrets.token_hex`),
  `compute_commitment`, `verify_reveal`: the core SHA-256 commit-reveal primitives.
  `SealedMove`/`CommitRevealLog` seal one entry per turn and audit the whole sequence.
- `crypto/step0.py` — `Step0Declaration`: seals `{team_code} + sysinfo` via the same
  commit-reveal primitive ("signed" = sealed via SHA-256, not an asymmetric signature — no
  such scheme was confirmed from the book text this session).
- `shared/sysinfo.py` — `collect_sysinfo()`: python_version/platform/processor/machine.
- `domain/negotiation.py` — `configs_match()`: the pre-game shared-config agreement check
  (byte-identical `config/game.json`, via the SHA-256 that already existed since stage 1).
- `runtime/peer_runtime.py` — `run_turn_loop` now seals every outbound move via
  `CommitRevealLog.seal()` before sending it.
- `cli.py declare` — new subcommand, manually run and confirmed printing a real sealed
  declaration with `verify() = True`.
- **Deliberately does not implement**: the wire-level Commit→Acknowledge→Reveal exchange
  *between* peers (needs the same synchronized turn-taking protocol already deferred since
  stage 3), or a full negotiation handshake beyond the config-match check. See
  `docs/PRD_security_crypto.md` for the reasoning.

Still no barrier-placement decisions, no real synchronized turn-taking, no live public
exposure — per the book's layering order and the design decisions above.

## Build stages (book's own priority order — each runs end-to-end before the next starts)
1. Base logic — grid, movement, barriers, capture, scoring. No networking. *(done)*
2. MCP infra — FastMCP server/client on localhost, no strategy yet. *(done)*
3. Blind strategy — heuristic move-decision (Manhattan distance), still no language/scent.
   *(done)*
4. Language + scent — pheromone math, free-text hints, LLM plugged in for banter text only.
   *(done)*
5. Cloud exposure + tunneling — ngrok, environment separation. *(done)*
6. Security — Commit-Reveal, Nonce, Step-0 hardware declaration, pre-game SHA-256
   agreement check. *(done)*
7. Reporting shell — Gmail OAuth2 + Gatekeeper, Live GUI, Replay Viewer. *(done)*

All 7 book-mandated build stages are now complete. What remains is the deferred integration
work tracked below (synchronized turn-taking, barrier placement, the live Gmail/ngrok setup)
— not a new stage, but the pieces those stages deliberately left as documented open items.

## Stage 7 — what was built
- `domain/game_ids.py` — `generate_game_id`/`artifact_filename`: id + filename scheme for the
  four mandatory artifacts (placeholder scheme pending the book's exact format).
- `report/artifacts.py` — `build_declaration/config/log/result`: four pure JSON builders.
- `report/report_writer.py` — `write_artifacts`: writes the four files to `logs/<group_id>/`.
- `shared/api_gatekeeper.py` — `TokenBucketGatekeeper` + `run_guarded`: token-bucket rate
  limiter + concurrency cap + retry/backoff, from `rate_limiter_gatekeeper` config.
- `infra/email_sender.py` — `build_message`/`send_report`: Gmail API message builder + send
  wrapper (`gmail.send` scope only); consumes an existing `token.json`, never obtains one.
- `gui/live_gui.py` — `LiveGui`: Tkinter grid + turn banner, local-truth-only (never an
  omniscient board).
- `gui/replay_viewer.py` — `ReplayViewer`/`load_log`/`verify_move`: step-through viewer
  re-verifying every move's SHA-256 commitment, "Verified OK"/"TAMPERED".
- `cli.py replay --log <path>` — new subcommand, opens the real replay viewer.
- `crypto/commit_reveal.py` gains `CommitRevealLog.entries()` for the report layer.
- **Manually verified the full pipeline end-to-end on disk**: real declaration + sealed moves
  → all four artifacts built and written to `logs/bb-ai-12/` → reloaded from disk → every
  move re-verified `True` → a reloaded move tampered with → `verify_move` correctly flips to
  `False`. See `docs/PRD_reporting_shell.md` for the exact transcript.
- **Deliberately did not build**: a `send-report` CLI command (no game-completion detection
  yet to source a real outcome from) or run the live Gmail OAuth setup (the user's own guided
  action — walkthrough steps are written and ready in `docs/PRD_reporting_shell.md`).

## Book re-verification pass — 2026-08-20
The book PDF turned out to be locally readable on this machine; re-read the relevant chapters
directly instead of leaving several items as open guesses. See `docs/TODO.md`'s "Done (book
re-verification pass)" section for the full detail. Headline results:
- **`num_games` resolved**: book Table 18 confirms `6`, status `קבוע` (FIXED/constant, not
  negotiable — deviation disqualifies the team). `config/game.json` was shipping the wrong
  value (`1`); fixed in both repos, byte-identity re-verified via `sha256sum`.
- **Fixed a real bug** in `crypto/commit_reveal.py`'s `compute_commitment`: the book's exact
  formula (ch.5.3) hashes the nonce *inside* the canonical JSON record, not concatenated
  outside it. Both repos corrected and re-tested.
- **Added `runtime/state_machine.py`** — `GamePhaseMachine`, reproduced from the book's own
  ch.8.3 example code — now actually wired into `PeerRuntime` (see the "Real turn-taking
  protocol" section below; the turn-alternation-vs-simultaneous-round question that blocked
  this got resolved too).
- Confirmed the Gatekeeper parameter table (book Table 19) matches this repo's
  `rate_limiter_gatekeeper` exactly — no changes needed there.
- Confirmed Step-0 (ch.5.5) mentions signing with "a key supplied in advance" — a real
  signing key may be intended, not necessarily the SHA-256 commit-reveal sealing this repo
  currently uses. No such key has been supplied yet; flagged as a sharper open question.

## Real turn-taking protocol — 2026-08-20 (closes the stage-2/3/6 deferred item)
Re-reading the book's ch.4.3 pheromone-decay section settled the open turn-alternation
question: decay runs "after both the cop and the thief have completed their move" — a "turn"
is a joint round, not chess-style alternation. That, plus ch.5.3's exact 4-step protocol and
ch.8.3's state machine, was enough to replace the STAY-echo stub with the real thing:
- `peer/turn_handler.py` — `TurnHandler`: per-round bookkeeping, raises on a reveal with no
  prior commit (the Ack step's actual enforced purpose).
- `mcp/server.py` rewritten as `build_server(name, turn_handler)`, exposing
  `submit_commit`/`submit_reveal` — replaces `receive_move` entirely.
- `mcp/client.py`'s `McpTransport` gains `send_commit`/`send_reveal`.
- `runtime/peer_runtime.py`'s `run_turn_loop` rewritten around the real per-round cycle,
  driven by `GamePhaseMachine`; a network failure at either send step lands the machine in
  `TECHNICAL_LOSS`.
- **Manually verified with a real two-process run — the first genuinely bidirectional
  exchange this session**: both peers committed, revealed their own real strategy-chosen
  moves and hints, and received the *opponent's* real reveal back (not a stub). See
  `docs/PRD_turn_protocol.md` for the full transcript and remaining design decisions
  (`intent` always `"truth"` for now, `state` snapshot shape, barrier/deception/negotiation
  still deferred).
- 117 tests, 93% coverage, ruff-clean.

## Automatic end-of-game detection — 2026-08-20 (closes the stage-7 deferred item)
`PeerRuntime.run_turn_loop` previously always ran exactly `--turns N` with no awareness of the
actual game rules. No new detection logic was needed — `domain.rules.outcome_after_step`
(stage 1) already answers "is the sub-game over, and how"; the only new piece was a small pure
mapper, `cop_and_thief_positions(role, own_position, opponent_position)`, translating a peer's
role-relative `BeliefState` into the rules layer's role-neutral `(cop_pos, thief_pos)` order:
- `domain/rules.py` gains `cop_and_thief_positions`.
- `runtime/peer_runtime.py`'s `PeerRuntime` gains `role: Role`/`survival_threshold: int`
  constructor params, `self.outcome`/`self.final_turn` state, and `_check_outcome(turn)`;
  `run_turn_loop` now stops early with a `GAME OVER: <outcome> — scores {...}` print the
  moment either capture or survival is reached.
- `cli.py` split into a `cli/` package (one module per subcommand) — the flat file hit the
  150-line cap once `role`/`survival_threshold` were added to the `peer` subcommand.
- Both peers independently reach the same CAPTURED/SURVIVED conclusion from the same round's
  honestly-revealed positions with no extra coordination message — a direct consequence of the
  P2P zero-shared-state design plus the existing honest-relay assumption.
- 122 tests, 93% coverage, ruff-clean. See `docs/PRD_end_of_game_detection.md` for the full
  design reasoning and acceptance criteria.
- **Live two-process verification was attempted and blocked by a real, pre-existing,
  100%-reproducible bug in the turn protocol** (not caused by this feature) — see
  `docs/PRD_end_of_game_detection.md` and the new high-priority open flag in `docs/TODO.md`.
  Verification instead relies on the unit-test suite, which directly exercises the same
  early-stop code path via a stubbed transport.

## Commit-reveal round-1 race — fixed 2026-08-20
The round-1 race flagged immediately above (two freshly-started independent peer processes
crashing on round 1) is fixed: `TurnHandler.wait_for_own_reveal` makes an inbound
`submit_reveal` call block (bounded by `reveal_wait_timeout_sec`, sourced from
`network_and_league.response_timeout_sec`) until this peer has locally prepared its own reveal
for that round, instead of failing immediately if it hasn't yet. Re-ran the exact live
two-process verification that surfaced the bug: 40-turn run, real bidirectional exchange every
round from turn 1 through turn 35 (previously died on round 1 both attempts), clean automatic
`GAME OVER: survived` detection on the police side, no stray processes left on the ports
afterward. 127 tests, 93% coverage, ruff-clean. That same run's thief-side exit hit a separate,
already-documented, lower-severity "benign teardown race" — also fixed the same day, see
immediately below.

## Benign teardown race — fixed 2026-08-20
`cli/peer.py` now sleeps `_SHUTDOWN_GRACE_SEC = 3.0` seconds before exiting once
`runtime.outcome` leaves `ONGOING`, keeping this peer's server alive long enough for the
opponent's straggling final-round call to land instead of hitting a torn-down connection.
Re-ran the two-process verification again: both processes now exit with code 0 and zero
errors, both independently printing `GAME OVER: survived`. See `docs/TODO.md` for full detail.

## Automatic send-report hook — 2026-08-24
`report/emit.py`'s `emit_report` (build → write → email) was always in the architecture
diagram above but had no caller — `PRD_reporting_shell.md` deliberately deferred wiring it
until a real `GameOutcome` existed. Both turn loops now produce one, so `cli/peer.py` and
`cli/league_peer.py` each call `emit_report` once their run leaves `outcome is ONGOING`,
sourcing the recipient from `config/game.toml`'s `[email].recipient` and the token from the
already-live-verified `token.json`. See `docs/TODO.md`'s "Done (automatic send-report hook)"
for the exact wiring per CLI subcommand and test coverage.

## Book re-verification pass #2 — 2026-08-24 (live PDF read this session)
The 2026-08-20 pass relied on pre-extracted text; this pass read `police_thief_p2p.pdf`
directly, page by page, to check the two long-standing open flags (Step-0 signing key,
commit-reveal formula deviation) and re-confirm three already-implemented parameter tables
(`num_games`, scoring, Gatekeeper — all unchanged, all correct). See `docs/TODO.md`'s "Done
(book re-verification pass #2)" for the exact quotes and page numbers, and
`docs/PRD_security_crypto.md` for the corrected Step-0 design-decision note.

## Open items / flags (tracked, not silently decided)
- `agreed_between` in `config/game.json` currently lists `"<opponent-team-code>"` as a
  placeholder — fill in the real opponent code once a match is negotiated, in both repos.
- `config/game.toml` `[game].members` lists placeholder student IDs — fill in real IDs.
