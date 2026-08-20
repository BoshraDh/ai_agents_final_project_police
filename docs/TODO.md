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

## Done (Stage 5 — Cloud exposure + tunneling)
- [x] Picked ngrok (documented one-time setup in `docs/PRD_cloud_tunnel.md`).
- [x] `mcp/tunnel.py` — `NgrokTunnel`, starts/stops the tunnel and reports the public URL.
- [x] `cli.py tunnel` subcommand — prints the public MCP URL, blocks until Ctrl+C.
- [x] Documented the environment separation between "localhost smoke test" (`peer`) and "real
      match over a public tunnel" (`tunnel`) in README.md.
- [x] 61 tests, 92% coverage, ruff-clean.
- [x] Updated this file, PLAN.md, PRD.md, PRD_cloud_tunnel.md, README.md.
- [x] **Explicitly did not run a live tunnel** — per a check-in with the user, that's her own
      action on match day (installing ngrok, creating an account, opening a public port are
      out of scope for this session to do unattended). See `docs/PRD_cloud_tunnel.md`.

## Done (Stage 6 — Security)
- [x] `crypto/commit_reveal.py` — canonical-JSON SHA-256 commit/verify, nonce via
      `secrets.token_hex`; `CommitRevealLog` seals + audits a full sub-game's moves.
- [x] `crypto/step0.py` — sealed hardware/software declaration (`shared/sysinfo.py`).
- [x] `domain/negotiation.py` — pre-game shared-config agreement check (`configs_match`).
- [x] `runtime/peer_runtime.py` seals every outbound move via `CommitRevealLog` before sending.
- [x] `cli.py declare` subcommand — manually run and confirmed real output, `verify()=True`.
- [x] 74 tests, 92% coverage, ruff-clean.
- [x] Updated this file, PLAN.md, PRD.md, PRD_security_crypto.md, README.md.
- [x] **Explicitly did not build**: the wire-level Commit→Acknowledge→Reveal exchange between
      peers, or `peer/handshake.py`/`peer/turn_handler.py` — both need the book's exact
      negotiation-protocol text re-confirmed first (see `docs/PRD_security_crypto.md`).

## Done (Stage 7 — Reporting shell)
- [x] `report/artifacts.py` — the four mandatory JSON artifact builders.
- [x] `report/report_writer.py` — writes the four files to `logs/<group_id>/`.
- [x] `infra/email_sender.py` — Gmail message builder + send wrapper (`gmail.send` scope
      only); consumes an existing `token.json`, never obtains one unattended.
- [x] `shared/api_gatekeeper.py` — token-bucket rate limiter + concurrency cap + retry/backoff,
      from `rate_limiter_gatekeeper` config.
- [x] `gui/live_gui.py` — local-truth-only Tkinter grid + turn banner.
- [x] `gui/replay_viewer.py` — step-through replay re-verifying SHA-256, "Verified OK"/
      "TAMPERED".
- [x] `cli.py replay --log <path>` subcommand.
- [x] Manually verified the full pipeline end-to-end on real files (declare → seal → build →
      write → reload → verify → tamper → re-verify) — see `docs/PRD_reporting_shell.md`.
- [x] 100 tests, 93% coverage, ruff-clean.
- [x] Updated this file, PLAN.md, PRD.md, PRD_reporting_shell.md, README.md.
- [x] **Explicitly did not build**: a `send-report` CLI command (needs game-completion
      detection first — still open, see below).
- [x] **Live Gmail OAuth setup — completed 2026-08-20, live with the user**: Google Cloud
      project + Gmail API enabled + OAuth consent screen + `credentials.json`/`token.json` in
      both repos, verified with a real send to `rmisegal+uoh26finalgame@gmail.com` via the
      live Gmail API (real message id returned). See `docs/PRD_reporting_shell.md`.

All 7 book-mandated build stages are now complete. Remaining work is the deferred
integration items below, plus playing real games once ready.

## Open flags (not blocking, must resolve before a real submission-counted match)
- [ ] **`num_games`** — confirm against the book text whether the mandated per-series value
      is `6` (as the reference repo's README claims) or the Appendix ו example `1`; update
      `config/game.json` in both repos together if it changes.
- [ ] Replace `agreed_between: ["bb-ai-12", "<opponent-team-code>"]` with the real opponent
      code once a match is negotiated (both repos, kept byte-identical).
- [ ] Replace `[game].members` placeholder student IDs in `config/game.toml`.
- [ ] **Synchronized turn-taking / negotiation handshake** — still open (`peer/turn_handler.py`,
      `peer/handshake.py`); `mcp/server.py`'s inbound `receive_move` still always echoes STAY.
      Re-check the book's exact protocol text before designing — see
      `docs/PRD_security_crypto.md`'s design-decision note (this now also blocks the
      wire-level Commit→Acknowledge→Reveal exchange between peers, not just move relay).
- [ ] **Barrier placement** — `PoliceBrain` only ever chooses a movement direction; it doesn't
      yet decide when/where to place a barrier, and the wire protocol doesn't carry barrier
      messages. Add once the message schema is extended (likely alongside the item above).
- [ ] **Pheromone spatial spread** — re-confirm the book's exact spatial falloff shape for
      `pheromone_grid_size` (uniform vs. weighted neighborhood deposit) before implementing
      anything beyond the current single-cell deposit in `domain/pheromones.py`.
- [ ] **Live ngrok tunnel** — `mcp/tunnel.py` is built and unit-tested but never run live this
      session (see `docs/PRD_cloud_tunnel.md`); the user runs `bb-ai-12-police tunnel` herself
      once ngrok is installed and she's ready for a real match.
- [ ] **Step-0 "signing"** — currently sealed via SHA-256 commit-reveal, not an asymmetric
      signature (none was confirmed from the book text this session). Revisit if the book
      specifies real public-key signatures for Step-0.
- [ ] **Game-completion detection / `send-report` command** — `PeerRuntime.run_turn_loop`
      still just runs exactly `--turns N`; it doesn't call `domain.rules.outcome_after_step`
      to detect capture/survival and stop with a real `GameOutcome`. Needed before a
      `send-report` CLI command can be built meaningfully (see `docs/PRD_reporting_shell.md`).
- [ ] **`cli.py` is at 145/150 lines** — the next subcommand needs the CLI split into a
      package (one module per subcommand) rather than one more function crammed in.

## Later stages (tracked here for visibility, detailed in their own PRD_*.md once started)
- [ ] Write the full 6-section academic report in README.md (rules model, communication
      approach, decision-making, LLM usage, live-GUI verification, replay-viewer
      verification) — the underlying code for all six now exists, per `docs/PLAN.md`.
- [ ] At least 2 full games played against a real opponent team before submission
      (`min_games_to_pass = 2`).
- [ ] `git tag -a v1.0-submission` once feature-complete.
