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

## Done (book re-verification pass — 2026-08-20)
The book PDF (and its pre-extracted text) turned out to be locally readable on this machine —
re-read the relevant chapters directly instead of leaving these as open guesses:
- [x] **`num_games` resolved: 6, and it is FIXED (not negotiable)** — book Table 18
      ("פרמטרי הרשת והליגה" / Network & League Parameters), row 1: "מספר המשחקונים בסדרה מול
      יריבה" (sub-games per series against one opponent) = `6`, status `קבוע` (constant).
      Deviating from a "constant"-status value disqualifies the team per the book's own status
      definitions. Fixed `config/game.json` in both repos from `1` to `6`; re-verified
      byte-identical via `sha256sum`. This was a real, disqualification-risk bug, not just an
      open question.
- [x] **Fixed a real cryptographic bug in `crypto/commit_reveal.py`**: the book's exact
      formula (ch.5.3, with a full Python `commit()`/`verify()` code sample) is
      `Hcommit = SHA256(canonical_json({...payload, "nonce": nonce}))` — the nonce is one more
      field *inside* the single canonically-serialized JSON record. `compute_commitment` was
      instead concatenating `canonical_json(payload) + nonce` as two separate strings, which
      produces a different (still internally-consistent, but not book-compliant) hash. Fixed
      to match the book exactly; added a test (`test_compute_commitment_matches_the_books_
      exact_formula`) that pins the byte-for-byte formula.
- [x] **Added `runtime/state_machine.py` — `GamePhaseMachine`**, reproduced from the book's
      own example code (ch.8.3, "Orchestrator and State Machine"), confirmed verbatim against
      the book text: `WAITING_FOR_OPPONENT → COMPUTING_MOVE → COMMITTING → AWAITING_REVEAL →
      VERIFYING → WAITING_FOR_OPPONENT`, with `TECHNICAL_LOSS` reachable from `COMPUTING_MOVE`
      or `AWAITING_REVEAL` as a terminal state. Not yet wired into `PeerRuntime` — see the open
      flag below.
- [x] 107 tests, 92% coverage, ruff-clean in both repos.
- [x] Confirmed (book Table 19, "Gatekeeper" parameters) that every other value already in
      `rate_limiter_gatekeeper` matches the book exactly: `requests_per_minute≥30`,
      `concurrent_requests≥2`, `retry_backoff_sec≥5`, `max_retries≥3`, `queue_depth≥100`,
      `response_timeout_sec=30` (negotiated), `watchdog_timeout_sec=60` (negotiated) — no
      changes needed there.
- [x] Confirmed the book's Step-0 section (ch.5.5) says the hardware/software declaration is
      "cryptographically signed using a key supplied in advance" (`מפתח המסופק מראש`) — this
      phrasing suggests a real pre-issued signing key may be intended, not necessarily the
      commit-reveal SHA-256 sealing this repo currently uses for Step-0. No such key has been
      supplied to this project yet, so `crypto/step0.py`'s current sealing approach is left as
      is (still the most defensible reading available), but this is now a *sharper* open
      question than before — see the open flag below.

## Open flags (not blocking, must resolve before a real submission-counted match)
- [ ] **Wire `GamePhaseMachine` into `PeerRuntime`** — the class exists and is tested, but
      `run_turn_loop` doesn't use it yet. Doing so properly also means redesigning the wire
      protocol around the book's confirmed 4-step Commit(hash-only)→Acknowledge(locked)→
      Reveal(move+hint, nonce still hidden)→Final-Reveal(all nonces, end of game only)
      sequence — a materially different shape from the current single `receive_move(direction,
      turn, hint)` stub. One thing the book text read this session did *not* settle: whether a
      "turn" is strict alternation (one agent moves, then explicitly hands off to the other —
      suggested by the Live GUI's green/gray "YOUR TURN"/"LOCKED" banner description) or a
      simultaneous joint round (suggested by the Dec-POMDP tuple's joint `P(s'|s,a1,a2)`).
      Re-check chapters 2-3 and the reference repo's actual `PeerRuntime` loop before building
      this — don't guess at the exchange order.
- [ ] **Step-0 "signing" key** — book ch.5.5 mentions signing with "a key supplied in
      advance"; no such key has been issued/found yet. Revisit if/when one is supplied (e.g.
      in a course announcement or the reference repo's own Step-0 code), and treat the current
      SHA-256-commit-reveal-based sealing as a placeholder until then.
- [ ] Replace `agreed_between: ["bb-ai-12", "<opponent-team-code>"]` with the real opponent
      code once a match is negotiated (both repos, kept byte-identical).
- [ ] Replace `[game].members` placeholder student IDs in `config/game.toml`.
- [ ] **Barrier placement** — `PoliceBrain` only ever chooses a movement direction; it doesn't
      yet decide when/where to place a barrier, and the wire protocol doesn't carry barrier
      messages. Add once the message schema is extended (likely alongside the turn-taking item
      above).
- [ ] **Pheromone spatial spread** — re-confirm the book's exact spatial falloff shape for
      `pheromone_grid_size` (uniform vs. weighted neighborhood deposit) before implementing
      anything beyond the current single-cell deposit in `domain/pheromones.py`.
- [ ] **Live ngrok tunnel** — `mcp/tunnel.py` is built and unit-tested but never run live this
      session (see `docs/PRD_cloud_tunnel.md`); the user runs `bb-ai-12-police tunnel` herself
      once ngrok is installed and she's ready for a real match.
- [ ] **Game-completion detection / `send-report` command** — `PeerRuntime.run_turn_loop`
      still just runs exactly `--turns N`; it doesn't call `domain.rules.outcome_after_step`
      to detect capture/survival and stop with a real `GameOutcome`. Needed before a
      `send-report` CLI command can be built meaningfully (see `docs/PRD_reporting_shell.md`).
- [ ] **`cli.py` is at 145/150 lines** — the next subcommand needs the CLI split into a
      package (one module per subcommand) rather than one more function crammed in.
- [ ] **Known test flakiness (environmental, not a code bug)**: `tests/gui/` occasionally hits
      `_tkinter.TclError: Can't find a usable init.tcl` under this Windows machine's file-I/O
      contention when many Tk interpreters are created/destroyed back-to-back in one `pytest`
      run. Re-running always passes cleanly; the GUI code itself is correct (verified via
      multiple clean full-suite runs). Not worth chasing further in this session.

## Later stages (tracked here for visibility, detailed in their own PRD_*.md once started)
- [ ] Write the full 6-section academic report in README.md (rules model, communication
      approach, decision-making, LLM usage, live-GUI verification, replay-viewer
      verification) — the underlying code for all six now exists, per `docs/PLAN.md`.
- [ ] At least 2 full games played against a real opponent team before submission
      (`min_games_to_pass = 2`).
- [ ] `git tag -a v1.0-submission` once feature-complete.
