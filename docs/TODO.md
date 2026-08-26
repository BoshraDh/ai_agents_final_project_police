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

## Done (real turn-taking protocol — 2026-08-20)
- [x] **Resolved the turn-alternation-vs-simultaneous-round question**: book ch.4.3 confirms
      pheromone decay runs "after both the cop and the thief have completed their move" for
      a turn — a joint round, not chess-style alternation.
- [x] `peer/turn_handler.py` — `TurnHandler`, real per-round protocol bookkeeping.
- [x] `mcp/server.py` rewritten (`build_server`, `submit_commit`/`submit_reveal`) — replaces
      `receive_move` entirely; `mcp/client.py` gains `send_commit`/`send_reveal`.
- [x] `runtime/peer_runtime.py`'s `run_turn_loop` rewritten around the real per-round cycle,
      driven by `GamePhaseMachine` (network failures → `TECHNICAL_LOSS`).
- [x] **Manually verified with a real two-process run — genuinely bidirectional**: both peers
      committed, revealed real strategy-chosen moves/hints, and received the *opponent's* real
      reveal back. See `docs/PRD_turn_protocol.md` for the full transcript.
- [x] 117 tests, 93% coverage, ruff-clean.
- [x] Updated this file, PLAN.md, PRD.md, PRD_turn_protocol.md, README.md.

## Done (automatic end-of-game detection — 2026-08-20)
- [x] `domain/rules.py` — `cop_and_thief_positions(role, own_position, opponent_position)`:
      maps this peer's role-relative `BeliefState` (own/opponent) into the rules layer's
      role-neutral `(cop_pos, thief_pos)` order that `outcome_after_step` expects.
- [x] `runtime/peer_runtime.py` — `PeerRuntime` now takes `role: Role` and
      `survival_threshold: int`; tracks `self.outcome` (`GameOutcome`, starts `ONGOING`) and
      `self.final_turn`. New `_check_outcome(turn)` calls `domain.rules.outcome_after_step` on
      the just-updated `BeliefState` after every round; `run_turn_loop` now stops early and
      prints a `GAME OVER: <outcome> — scores {...}` line (via `domain.scoring.scores_for_both`)
      the moment either capture or survival is reached, instead of always running the full
      requested `--turns N`.
- [x] `cli.py` split into a `cli/` package (`__init__.py`, `check_config.py`, `peer.py`,
      `tunnel.py`, `declare.py`, `replay.py`) — the flat file hit the 150-line cap once
      `role`/`survival_threshold` were added to the `peer` subcommand's `PeerRuntime` call;
      `cli/peer.py` now hardcodes `role=Role.POLICE` and reads `survival_threshold` from
      `config/game.json`'s `movement_and_barriers.survival_threshold`.
- [x] Both peers can independently reach the same CAPTURED/SURVIVED conclusion from the same
      round's honestly-revealed positions with no extra coordination message — a direct
      consequence of the P2P zero-shared-state design plus the existing honest-relay
      assumption; documented in `runtime/peer_runtime.py`'s module docstring.
- [x] 12 new/updated tests (`cop_and_thief_positions` x2, early-stop-on-capture,
      early-stop-on-survival, stays-ongoing-when-the-turn-cap-is-hit-first, plus the flexible
      `_runtime()` fixture all existing tests now share) — 122 tests, 93% coverage, ruff-clean.
- [x] **Found a real, 100%-reproducible protocol bug while attempting the live two-process
      verification for this feature** — see the new open flag below (not caused by this
      feature; pre-existing in the commit-reveal turn protocol since the last stage).
- [x] Updated this file, PLAN.md, PRD.md, README.md in both repos.

## Done (commit-reveal round-1 race — fixed, 2026-08-20)
- [x] **Fixed the round-1 race flagged in the previous entry.** Root cause was confirmed: the
      book's Acknowledge step ("ensure reveal only after BOTH sides have committed") was never
      actually enforced — `submit_reveal` answered immediately, which only worked if the
      opponent happened to have already raced ahead to prepare its own reveal locally first.
- [x] `peer/turn_handler.py` — `TurnHandler.wait_for_own_reveal(turn, timeout_sec,
      poll_interval_sec=0.02)`: blocks (short polling loop) until this peer has locally
      prepared its own round-`turn` reveal, raising `TimeoutError` if that never happens within
      `timeout_sec`. Turns the previous race into an implicit rendezvous: an inbound
      `submit_reveal` call now waits for this peer to catch up instead of failing immediately.
- [x] `mcp/server.py` — `build_server` gains `reveal_wait_timeout_sec: float = 30.0`;
      `submit_reveal` calls `wait_for_own_reveal` instead of the old immediate `own_reveal`
      lookup. `submit_reveal` still raises immediately (unchanged) if no commit preceded it —
      that check was never the source of the race.
- [x] `runtime/peer_runtime.py` — `PeerRuntime` gains `reveal_wait_timeout_sec: float`, passed
      through to `build_server` in `start_server`.
- [x] `cli/peer.py` — passes `reveal_wait_timeout_sec=shared["network_and_league"]
      ["response_timeout_sec"]` (reuses the existing book-mandated config value, `30`, rather
      than inventing a new constant — NFR-4).
- [x] 6 new/updated tests (turn_handler: returns-immediately / blocks-until-another-thread /
      times-out; mcp/server: waits-for-another-thread / times-out) — 127 tests, 93% coverage,
      ruff-clean.
- [x] **Re-ran the live two-process verification that originally surfaced the bug — now
      succeeds.** `bb-ai-12-police peer --turns 40` + `bb-ai-12-thief peer --turns 40`, both
      started as independent processes: real bidirectional commit-reveal exchange every round
      from turn 1 through turn 35 (previously died on round 1, 2/2 attempts), police correctly
      auto-detected `GAME OVER: survived — scores {'police': 5, 'thief': 10}` at turn 35 and
      exited cleanly (exit 0). No stray processes left bound to ports 8801/8802 afterward.
- [x] **Thief's process exited with an error at turn 35** — the *different*, already-documented
      "benign teardown race" (since stage 2: "the shorter-running side's script exits
      mid-flight"), not the round-1 bug: whichever side reaches `GAME OVER` first was exiting
      immediately with no grace period, so the other side's in-flight final-round outbound call
      could land after that server had already torn down. **Also fixed, same day** — see below.

## Done (benign teardown race — fixed, 2026-08-20)
- [x] `cli/peer.py` — after `run_turn_loop` returns, if `runtime.outcome` is no longer
      `ONGOING` the process now sleeps `_SHUTDOWN_GRACE_SEC = 3.0` seconds before exiting,
      keeping this peer's (daemon-thread) server alive long enough for the opponent's
      straggling final-round call to land, instead of exiting the instant the local loop ends.
- [x] Re-ran the live two-process verification once more: both `bb-ai-12-police peer --turns
      40` and `bb-ai-12-thief peer --turns 40` now exit with code 0 and zero errors in either
      log — both sides independently printed `GAME OVER: survived — scores {'police': 5,
      'thief': 10}` at turn 35. No stray processes left on ports 8801/8802 afterward.
- [x] 127 tests, 93% coverage, ruff-clean (no test file changes needed — this is a thin,
      CLI-layer timing fix with no new branching logic to unit test beyond what coverage
      already exercises indirectly).
- [x] Not a mathematically airtight fix (a sufficiently slow opponent could still in theory miss
      a 3-second window), but reduces the failure window from "always, if timing is close" to
      "a multi-second grace period," which matched the "fix it if it's easy" ask — a fully
      deterministic fix (e.g. an explicit final handshake before either side may exit) is a
      larger protocol change, not pursued here.

## Open flags (not blocking, must resolve before a real submission-counted match)
- [ ] **Step-0 "signing" key — CONFIRMED by direct book read, 2026-08-24.** §5.5, p.39–40:
      "המפרט כולו נארז למחרוזת JSON ונחתם קריפטוגרפית באמצעות מפתח המסופק מראש, כך שלא ניתן
      לזייפו בדיעבד" — "the entire spec is packed into a JSON string and cryptographically
      signed using a key supplied in advance, so it cannot be forged after the fact." This is
      now verified against the actual PDF text (not secondhand), and it describes a real
      keyed-signature mechanism, distinct from this repo's unkeyed SHA-256 commit-reveal
      sealing. No such key has been issued/found yet. Revisit if/when one is supplied (e.g. in
      a course announcement or the reference repo's own Step-0 code — neither checked this
      session), and treat the current sealing as a placeholder until then.
- [ ] Replace `agreed_between: ["bb-ai-12", "<opponent-team-code>"]` with the real opponent
      code once a match is negotiated (both repos, kept byte-identical).
- [ ] Replace `[game].members` placeholder student IDs in `config/game.toml`.
- [ ] **Barrier placement** — `PoliceBrain` only ever chooses a movement direction; it doesn't
      yet decide when/where to place a barrier, and the commit-reveal wire protocol's `state`/
      `move` fields don't carry barrier messages yet. Add once the schema is extended.
- [ ] **Deceptive hints** — the real turn protocol's `intent` field ("truth"/"lie") is now
      wired end-to-end over the wire, but nothing ever sets it to `"lie"` yet — `TemplateProvider`
      lines aren't factual claims. FR-8's thief-deception allowance needs real position-claim
      logic behind this field. See `docs/PRD_turn_protocol.md`.
- [ ] **Real negotiation handshake beyond config-agreement** — `domain.negotiation.
      configs_match` only checks `config/game.json` byte-identity; game_id assignment and any
      other pre-game agreement steps aren't built.
- [ ] **Mutual end-of-game audit exchange** — each peer's `CommitRevealLog` already
      self-audits; peers don't yet exchange final logs with each other for a true *mutual*
      audit (book ch.5.4).
- [ ] **Pheromone spatial spread** — re-confirm the book's exact spatial falloff shape for
      `pheromone_grid_size` (uniform vs. weighted neighborhood deposit) before implementing
      anything beyond the current single-cell deposit in `domain/pheromones.py`.
- [ ] **Live ngrok tunnel** — `mcp/tunnel.py` is built and unit-tested but never run live this
      session (see `docs/PRD_cloud_tunnel.md`); the user runs `bb-ai-12-police tunnel` herself
      once ngrok is installed and she's ready for a real match.
- [ ] **Known test flakiness (environmental, not a code bug)**: `tests/gui/` occasionally hits
      `_tkinter.TclError: Can't find a usable init.tcl` under this Windows machine's file-I/O
      contention when many Tk interpreters are created/destroyed back-to-back in one `pytest`
      run. Re-running always passes cleanly; the GUI code itself is correct (verified via
      multiple clean full-suite runs). Not worth chasing further in this session.

## Done (deliberate switch to the league's shared commit formula — 2026-08-24)
- [x] **`crypto/commit_reveal.py`'s `compute_commitment` changed from the book's ch.5.3 literal
      formula to the `copthief-league-protocol` kit's formula** (nonce pipe-concatenated
      *outside* the canonical JSON, `ensure_ascii=False`), a conscious, explicitly-weighed
      deviation from the book — see the module docstring for the exact before/after formulas.
      Confirmed against the kit's own `verify_vectors.py` source (`ref_commit`), not a
      paraphrase.
- [x] **Why**: live negotiation with two real opponent teams this session (SMNGRP05,
      and earlier the imreeyal/anrbj666 pairing) surfaced that the actual opponent pool in
      this league has converged on this kit's formula rather than the book's literal one —
      confirmed directly by SMNGRP05 rereading the book themselves mid-negotiation and
      admitting "we have been treating a third-party kit as if it were the specification."
      Matching the book exactly, as this repo did until now, means failing every real
      audit against that pool. The user made an explicit, informed choice to prioritize
      being able to actually play a real match over strict book-formula compliance, after
      being told directly this trades away conformance to the graded specification.
- [x] `canonical_json` gains `ensure_ascii=False`.
- [x] Tests: `test_compute_commitment_matches_the_league_kits_exact_formula` replaces the old
      book-formula-pinning test; added `test_canonical_json_does_not_escape_non_ascii`.
      127 tests police / 128 tests thief, ruff-clean both.
- [x] **`config/game.toml` (thief) — `my_port` changed from 8801 to 8802**, matching police's
      port. Reason: our free-tier ngrok account only supports one live public hostname at a
      time; pointing both peers at the same local port lets one ngrok tunnel serve whichever
      of our two processes is actually running at a given moment (they're never run
      simultaneously against the same opponent). Updated the 3 tests that hardcoded 8801.
- [x] **Not changed**: the wire message shape/timing (still per-round `submit_commit`/
      `submit_reveal`, matching the book's step 3/4 reveal timing) and the tool names
      themselves — SMNGRP05's 4-tool, audit-only-reveal shape was evaluated and explicitly
      NOT adopted; see the SMNGRP05 negotiation thread for the full reasoning (it would make
      this repo's real-time capture/survival detection unable to fire mid-game).

## Done (league kit 4-tool protocol adapter — 2026-08-24)
- [x] New `league/` package: `terms.py`, `smell.py`, `inbox.py`, `server_tools.py`, `client.py`,
      `messages.py`, `outcome.py`, `runtime.py` (`LeagueRuntime`) — an **alternate, opt-in**
      transport for opponents (SMNGRP05 and others in this league) that run the
      `copthief-league-protocol` kit's 4-tool shape (`negotiate`/`receive_turn`/`submit_audit`/
      `receive_control`) instead of this repo's own `submit_commit`/`submit_reveal`. New
      `cli/league-peer` subcommand. Full design/reasoning in `docs/PRD_league_adapter.md`.
- [x] Real position is never disclosed mid-game under this protocol — only a probabilistic
      `smell_grid`. `league/smell.py`'s `guess_position_from_smell` feeds that to the
      unmodified `HeuristicBrain`; capture uses an explicit `capture_claim`/`claim_response`
      exchange instead of position equality (independently matches book rules 46/47, found
      while cross-checking the book this session); survival is thief-self-declared via
      `win_claim`.
- [x] `domain/pheromones.py` gains `PheromoneField.as_dict()` (read-only snapshot, needed to
      serialize `smell_grid`).
- [x] `to_wire_terms` output verified byte-for-byte against SMNGRP05's own canonical terms
      string — the handshake's exact-dict-equality gate passes.
- [x] **Real two-sided smoke test** (both repos' actual code, real local FastMCP servers, real
      network calls, not mocks): full `negotiate → per-round exchange → win_claim →
      submit_audit` cycle completed; both sides independently agreed the terms matched and
      arrived at the identical outcome (`survived`) at the identical `final_turn` — proof the
      protocol is genuinely symmetric, not just that one side's code runs.
- [x] 157 tests (29 new), 91% coverage, ruff-clean.
- [x] Explicitly out of scope: barrier-based capture, real `receive_control` handling, strict
      negotiate-mismatch refusal, independently re-verifying the opponent's audit records
      against their commits. See `docs/PRD_league_adapter.md`'s "Explicitly out of scope"
      section.

## Done (league adapter hardening from real live matches vs SMNGRP05 — 2026-08-24)
- [x] `LeagueRuntime.play` no longer lets a `TimeoutError` on the final exchange crash the
      whole process before `submit_audit` is ever sent — found live after a real ~40-round
      match against SMNGRP05's server died with an unhandled exception right at the survival
      boundary. Now: if our own `win_claim` condition was already met locally, conclude
      `SURVIVED` and still attempt `_send_audit` (best-effort, its own try/except).
      `turn_timeout_sec` default raised 30.0 → 60.0.
- [x] `_send_audit`'s result is no longer silently swallowed (`except Exception: pass`) — found
      live when SMNGRP05 reported "no audit payload arrived" on a run that exited clean on our
      side with no visible error. Now logs `[league] submit_audit reply: ...` on success or
      `[league] submit_audit failed: ...` on failure, and `_send_audit` returns the reply dict.
      (Root cause on their end turned out to be their own `audit_send_timeout_seconds` — fixed
      on their side; our logging change is what surfaced the mismatch either way.)
- [x] `build_negotiate` now sends `role` and `sub_game_number` — found live as a real gap: our
      negotiate message never included `sub_game_number` at all (config had the field, nothing
      read it), so every retry against an opponent whose own counter had advanced past 1 got
      silently dropped by their anti-replay check, requiring a manual synchronized restart each
      time. `LeagueRuntime.negotiate(sub_game_number=1)` and `cli league-peer --sub-game N` (else
      falls back to `config/game.toml`'s `[game].sub_game_number`) let a real multi-game series
      advance the number correctly instead of always sending 1.

## Done (automatic send-report hook — 2026-08-24)
- [x] **New `report/emit.py` — `emit_report(...)`**: builds all four mandatory artifacts
      (`build_declaration/config/log/result`), writes them via `report_writer.write_artifacts`,
      then emails them via `infra.email_sender.send_report`, guarded by
      `TokenBucketGatekeeper`/`run_guarded` (rate-limit + retry/backoff). A failed send is
      logged and swallowed, not fatal — the four artifacts are already safely on disk by then,
      so a Gmail hiccup must never crash a peer process right after a real game outcome.
- [x] `cli/peer.py` — after `run_turn_loop` returns with `runtime.outcome is not ONGOING`,
      calls `emit_report` before the shutdown-grace sleep. Since `PeerRuntime` never runs a
      real Step-0 exchange yet (a pre-existing gap, see the Step-0 open flag above), the
      declaration artifact uses a fresh `Step0Declaration.create(group_id)` at report time,
      same pattern as the standalone `declare` subcommand.
- [x] `cli/league_peer.py` — after `asyncio.run(_play(...))` returns with `runtime.outcome is
      not ONGOING`, calls `emit_report` using `LeagueRuntime`'s own `step0`/`commit_log`/
      `group_id` (already real, from the actual negotiated match).
- [x] Recipient read from `config/game.toml`'s existing `[email].recipient`; `token_path` is
      `<repo_root>/token.json`, the same live-verified OAuth token from the stage-7 Gmail setup
      (2026-08-20) — no new credential or setup step needed.
- [x] 2 new tests (`tests/report/test_emit.py`): a successful build+write+send round trip
      (asserts all 4 attachments exist and were sent), and a send failure that still leaves all
      4 artifacts on disk and logs the error instead of raising. 162 tests, 90% coverage,
      ruff-clean in both repos.
- [x] **Not run live yet** — needs a real finished match to trigger; the next real game played
      against an opponent will be the first live end-to-end proof (build → write → email) of
      this hook, same "verify for real, not just in a unit test" bar as every other stage.

## Done (book re-verification pass #2 — 2026-08-24, live PDF read this session)
Unlike the 2026-08-20 pass (which relied on pre-extracted text), the actual
`police_thief_p2p.pdf` was read directly, page by page, this session, to check the two open
flags below plus re-confirm three already-implemented parameters:
- [x] **Step-0 signing key** — the open flag two sections below is now upgraded from
      "book ch.5.5 mentions..." to a verified exact quote with page number (§5.5, p.39–40). Real,
      still-open gap: no key exists yet.
- [x] **Commit-reveal formula deviation** — the open flag near the end of this file now cites
      the actual mandatory/disqualifying rule (Appendix ה, Table 9, rule #17, p.129) verbatim.
      Conclusion: the deviation's risk is lower than previously assumed (disqualification is
      tied to *having no* SHA-256 commit-reveal mechanism, not to the exact byte formula), but
      not zero if the grader's own tooling recomputes hashes independently.
- [x] Re-confirmed unchanged, no code/config changes needed: `num_games=6` fixed (Appendix ו,
      Table 18 rule 1, p.138); the full scoring table 20/5/5/10/2 (Table 17, p.138); every
      Gatekeeper parameter (Table 19, p.139) — all match `config/game.json` exactly.
- [x] `docs/PRD_security_crypto.md`'s Step-0 design-decision note corrected — it previously
      claimed the book "does not confirm" a signing scheme; that was written without having
      read the book directly and is now fixed to cite the real quote.

## Done (`--friendly` flag on `league-peer` — 2026-08-24)
- [x] `league-peer --friendly` skips the automatic `emit_report` call for uncounted practice
      games — needed because `emit_report` doesn't otherwise distinguish counted vs. uncounted
      matches, and would otherwise email the grader's inbox (`config/game.toml`'s
      `[email].recipient`) for a friendly/dry-run series too. `cli/league_peer.py`'s `run` gains
      a `friendly: bool = False` param; `cli/__init__.py` wires the new `--friendly` argparse
      flag through. 2 new CLI-level tests (flag threads through / defaults to `False`). 164
      tests, ruff-clean, both repos.
- [x] **Not built**: a real "run all 6 sub-games unattended" orchestrator inside either repo's
      own code — deliberately kept as an external, uncommitted local script instead (not part
      of the graded submission), since it just shells out to each repo's existing
      `league-peer` CLI in sequence and needs no protocol/runtime changes.

## Done (fixed real audit-failing bug in the Step-0 system record — 2026-08-24)
- [x] **Root cause, independently verified (not taken on the opponent's word):** SMNGRP05
      reported, after a friendly 6/6 dry-run series, that our Step-0 declaration record failed
      their audit's commitment check (`failed_steps: [-1]`, `35 of 36 verified`). Traced this
      to our own code: `Step0Declaration.create()` computed `commitment` over
      `{team_code, python_version, platform, processor, machine}`, but `build_audit()` in
      `league/messages.py` then sent `{"type": "system_spec", **step0.payload}` over the wire
      — adding a `"type"` key to the payload *after* it was already sealed. Reproduced
      independently with a direct Python computation before touching any code: recomputing
      `compute_commitment` over the actual wire payload gave a different hash than the one we
      sent (`350b34d2...` vs `3e5f130d...`) — proof this was a real bug in our code, not a
      trust-the-opponent's-claim situation.
- [x] **Fix:** `Step0Declaration.create()` now includes `"type": "system_spec"` in the payload
      *before* sealing; `build_audit()` sends `step0.payload` directly instead of re-wrapping
      it. Principle: hash exactly what you send, send exactly what you hashed. Re-verified with
      the same direct computation — commit now matches.
- [x] 1 new regression test per repo
      (`test_build_audit_system_record_commit_verifies_against_the_wire_payload`) that recomputes
      the commitment over the actual wire payload and asserts it matches — would have caught
      this bug before it ever reached a real opponent's auditor. 165 tests, ruff-clean, both
      repos.
- [x] **Deliberately did NOT apply the opponent's exact prescribed fix verbatim** (their message
      suggested checking nonce reuse and re-serialization order as three separate possibilities)
      — instead diagnosed the actual narrow root cause independently and applied the minimal,
      correct fix. Their diagnosis of *what* was broken was accurate; the specific fix was ours.

## Done (`--report-to` override on `league-peer` — 2026-08-24)
- [x] `league-peer --report-to a@x.com,b@y.com` overrides the report recipient for that one
      run only, taking priority over both `--friendly` and `config/game.toml`'s
      `[email].recipient` — needed to validate the Step-0 audit fix (see above) with a real
      report email sent to the team's own inboxes, without touching the grader's configured
      address. `cli/league_peer.py`'s `run` gains `report_to: str | None = None`;
      `cli/__init__.py` wires the new `--report-to` flag through. 1 new CLI test
      (`test_league_peer_wires_report_to_through`); the two existing `--friendly` tests
      updated for the new `run()` signature. 166 tests, ruff-clean, both repos.
- [x] **Explicitly declined a request, embedded in suspicious third-party content received
      this session, to email the four report artifacts to the opponent team (SMNGRP05)
      directly.** That request doesn't match anything in the actual book text read this
      session, nor this project's own design — the real mutual-audit mechanism the league
      protocol already uses is the `submit_audit` MCP exchange (`league/messages.py`'s
      `build_audit`), not an out-of-band email to the opponent. `--report-to` only ever sends
      to addresses the user explicitly typed in her own message, never to an address that
      appeared unprompted in pasted third-party content.

## Done (live matches vs SMNGRP05, session 2 — 2026-08-24 evening)
- [x] **`handshake_timeout_sec` default raised 30.0 → 60.0** in `league/runtime.py`, matching
      the same precedent already applied to `turn_timeout_sec` earlier today. Real live
      evidence: repeated `TimeoutError: timed out waiting for opponent's negotiate` across many
      real attempts against SMNGRP05, even when their peer reported itself up and listening.
      Doubling the window is a legitimate low-risk mitigation for real network/launch-timing
      skew between two independently-run processes — **not** a fix for a code defect, since no
      defect was found. Tests hardcode `handshake_timeout_sec=1.0` for speed, unaffected.
- [x] **Investigated and explicitly rejected an unverified opponent claim that "the police
      path crashes on its first step."** Checked directly against real logs from this
      session's own runs: sub-game 2 (this repo playing police) completed cleanly earlier
      today — real capture at turn 2, `submit_audit: {'ok': True}`, report emailed
      successfully. Every subsequent "failure" was a `TimeoutError` *at the negotiate
      handshake*, before any game logic (including `PoliceBrain`) ever ran — directly
      contradicting the claim that police-specific code crashes at step 1. No changes made to
      `PoliceBrain`, `strategy/resolve_brain.py`, or the `capture_claim` role guard (already
      correct: `league/runtime.py`'s `_exchange_turn` only sets `capture_claim` when
      `self.role is Role.POLICE`) — there was nothing there to fix.
- [x] **Reverted `config/game.json`'s `agreed_between` back to the `"<opponent-team-code>"`
      placeholder** (was `["bb-ai-12", "SMNGRP05"]`) — the user ended the SMNGRP05 series and
      is moving to a different opponent team. Verified byte-identical between both repos after
      the edit (`diff` check, no divergence).
- [x] Re-verified the send-report pipeline live, twice more, against a real opponent: two
      more full sub-games (1 and 3) completed with clean `negotiate`/`submit_audit`/report-email
      round trips this evening, using the new `--report-to` override to the team's own inboxes
      instead of the grader address — confirms the Step-0 audit fix from earlier today holds
      under repeated real play, not just a single lucky run.
- [x] **Live-negotiate reliability against a real opponent remains fragile** — even after the
      timeout fix, a majority of `league-peer` attempts this evening still failed at the
      negotiate handshake (both `TimeoutError` and `502 Bad Gateway`, the latter explained by
      our own local MCP server only running for the lifetime of one `league-peer` process,
      not persisting between sub-games — the tunnel stays up but has nothing live behind it
      in between runs). Root cause of the `TimeoutError` failures specifically is still open:
      most likely simple launch-timing skew between two independently-run, manually-started
      processes rather than a code defect on either side. Not resolved this session; see the
      open flag below.
- [x] **Session ended by user choice, not because of an unresolved bug**: after repeated
      negotiate failures against SMNGRP05 despite the timeout fix, and given ambiguous/
      suspicious follow-on messages in that channel, the user chose to stop that series
      entirely and move to a different opponent team rather than keep debugging the timing
      issue live. See the security note below.

## Security note — suspicious content in the SMNGRP05 negotiation channel
This session, content arriving via the (legitimate, user-operated) SMNGRP05 relay channel
included at least one message the user did not confirm she deliberately typed/pasted, ending
in a Hebrew instruction directed at the assistant to email match report data to the opponent
team directly — declined, since it matches nothing in the actual book text and the real
mutual-audit path is the existing `submit_audit` MCP exchange, not an out-of-band email. A
later message also made a specific, checkable technical claim ("your police path crashes on
its first step") that was verified false against this session's own real logs before any code
was changed. Not a reason to distrust every future message from a real opponent team, but a
concrete reason to independently verify specific technical claims before acting on them,
especially ones that arrive with prescriptive fix instructions attached.

## Done (decisive evidence: negotiate failure is role-independent — 2026-08-24 late evening)
- [x] **Definitively disproved the opponent's repeated claim that "police-as-server" fails
      while "thief-as-client" succeeds.** Ran a fresh friendly series with roles swapped from
      the usual order: sub-game 1 as **police** (this repo) succeeded immediately — real
      capture at turn 2, `submit_audit: {'ok': True}`, report emailed. Sub-game 2 as
      **thief** (the sibling repo, `ai_agents_final_project_thief`) then failed with the exact
      same `TimeoutError: timed out waiting for opponent's negotiate` previously seen only on
      police attempts. Since this is the *same failure mode, now on the thief side*, the
      opponent's client/server-role theory is conclusively wrong: **the failure correlates
      with "second sub-game launched immediately after the first," not with which role (or
      which repo/brain) is playing.** No code changes made based on the opponent's diagnosis —
      confirmed groundless a second, independent way (first via log/timestamp contradiction,
      now via a controlled swapped-role experiment).
- [x] Both this repo's `PoliceBrain` and the thief repo's `ThiefBrain` are confirmed working
      correctly under real play (real capture, real 35-turn survival, real passing audits) —
      not "broken and never fixed" as repeatedly claimed via the SMNGRP05 channel.

## Open flag — negotiate-handshake reliability against a real opponent
- [ ] **Repeated live `TimeoutError`/`502` failures at the `negotiate` step against a real
      opponent, not reproduced in any unit test.** Doubling `handshake_timeout_sec` (30→60s,
      done this session) did not resolve it. Suspected cause: two independently, manually
      launched processes on two different machines need to hit "listening" within the same
      window, and there is no retry/backoff — a single missed window is a hard failure with no
      automatic recovery. Consider before the next real match: (a) an explicit
      "wait-then-retry" loop around one sub-game attempt instead of manual re-runs, (b) logging
      the exact wall-clock time each side's negotiate is sent/received to actually localize
      the skew, (c) confirming from a *third* real opponent whether this is peer-pair-specific
      or general.
- [ ] **This repo's commit-reveal formula no longer matches the book's ch.5.3 literal code
      sample.** If book-formula compliance turns out to matter more for grading than being
      able to complete a real match, this is a one-function revert (see git history /
      the module docstring's "before" formula) — not a design dead-end, a live, reversible
      trade-off made under time pressure the night before a deadline.
      **Risk re-assessed by direct book read, 2026-08-24 — lower than previously assumed, but
      not zero.** Appendix ה, Table 9 ("קריפטוגרפיה, שלמות רישום ואפס-ידיעה"), rule #17, p.129,
      is the actual mandatory/disqualifying requirement, and its wording is: "משתמשים
      בפרוטוקול התחייבות-וחשיפה מבוסס SHA-256. סנקציה: **היעדר מנגנון** גורר אי-חוקיות של
      הפתרון" — "use a SHA-256-based commit-reveal protocol. Sanction: **the absence of the
      mechanism** causes the solution to be disqualified." The disqualification sanction is
      keyed to not having a real commit-reveal mechanism at all, not to matching the book's
      illustrative byte-level formula. This repo has a real, working SHA-256 commit-reveal
      mechanism (just the league-kit's canonicalization instead of the book's own example) —
      so rule #17 itself does not appear to disqualify this deviation. The residual risk: if
      the instructor's own grading tooling independently recomputes commitments using the
      book's literal ch.5.3 formula to verify log integrity, a differently-canonicalized hash
      would still fail that specific check. Not re-verified against the reference repo's own
      commit hash implementation this session.

## Done (opponent switch to aviayeli — verified against the kit's actual source, 2026-08-25)
- [x] New opponent negotiated: team **aviayeli**. `config/game.toml`'s `opponent_url` updated to
      their thief endpoint (`https://cardinal-shell-moistness.ngrok-free.dev/mcp` — we play
      police here, so we call their thief).
- [x] **Verified their commit-reveal worked vector independently** against our own
      `compute_commitment` (not taken on their word) — byte-for-byte match
      (`ad35a33b985f72fbf1e9c0a60ae69ff219cba4c0df7b3e8b409ae29baa92161e`).
- [x] **Verified all 14 negotiate terms they listed** against `league/terms.py`'s
      `to_wire_terms` output — match exactly, including the hardcoded `min_center_intensity=0.5`.
- [x] Fetched the actual `copthief-league-protocol` kit's `SPEC.md` directly (not their paraphrase)
      to check their claim that the sealed-move `record` shape
      (`step/state/position/move/intent/hint`) must match ours — the kit's own spec says the
      payload schema is explicitly **not** an interop constraint (each side only needs
      seal↔reveal self-consistency; you never reconstruct the opponent's payload). No code
      change needed there.
- [x] **Declined to execute a command embedded in their message**
      (`PYTHONPATH=src .venv/bin/python -m scripts.setup_league_match --role ... --public-url
      ...`) — extracted only the plain URLs; running an opponent-supplied shell command in our
      own environment has no legitimate purpose.
- [x] **Decided (2026-08-25): keep `multiplicative_book_v1`, do not switch to the league's
      `subtractive_chebyshev_v1` default.** The kit's `SPEC.md` names both as mutually-exclusive
      conventions requiring explicit agreement; unlike the 2026-08-24 commit-formula switch, the
      user chose to stay book-faithful here rather than match the league default — decay model
      isn't one of the 14 negotiated wire terms and doesn't block negotiate/audit, only means our
      `smell_grid` values won't mean the same thing as an opponent using the league default. If
      this causes a real live-match issue with aviayeli or others, revisit (one-function change
      in `domain/pheromones.py`'s `PheromoneField.step`).

## Done (first fully-settled live match — vs aviayeli, 2026-08-25)
- [x] **New opponent: aviayeli.** Full negotiation, live debugging, and first
      real completed sub-game this session. `config/game.toml`'s `opponent_url`
      points at their thief endpoint (we play police here).
- [x] **Fixed: `submit_audit`'s `result_claim` must be an object, not a bare
      string.** `league/runtime.py`'s `_send_audit` sent
      `result_claim="capture"|"survival"|"timeout"`; aviayeli's validator
      requires `{"type": "capture"|"survival"|"timeout"}`, matching the
      existing `win_claim` object convention already used elsewhere in this
      protocol. Fixed in both repos; `tests/league/test_runtime.py` updated
      (2 tests) to assert the object shape.
- [x] **Fixed: `LeagueTransport`'s outbound calls read `result.data`, which is
      `None` unless the remote tool declares a strict output schema — ours and
      aviayeli's both return plain `dict[str, Any]`, so `.data` was always
      `None` even on success.** The real content is in `result.structured_content`.
      Fixed all four `LeagueTransport` methods (`negotiate`/`send_turn`/
      `send_audit`/`send_control`) to read `result.structured_content or
      result.data`. Found by adding temporary raw-result logging and reading
      the actual `CallToolResult` — the fallback still didn't surface content
      because the real payload sits in `.content[0].text` as a JSON string
      when no output schema is declared either; not fixed further since
      `.structured_content`/`.data` cover any opponent that *does* declare a
      schema, and the temporary content-level debug logging (removed after
      diagnosis) was what actually resolved the aviayeli exchanges.
- [x] **Fixed: `cli/league_peer.py` had no shutdown-grace period after the
      play loop.** `cli/peer.py` (the book-protocol path) already had this
      exact fix from the 2026-08-20 "benign teardown race" stage
      (`_SHUTDOWN_GRACE_SEC`, lingering after the local loop ends so the
      opponent's in-flight final call still finds a live server) — it was
      never ported to this league-adapter path. Found live: aviayeli's closing
      `submit_audit` to us got a 502 right as our process exited immediately
      after sub-game 1 finished. Added `_SHUTDOWN_GRACE_SEC = 5.0` and a
      `time.sleep()` right after `asyncio.run(_play(...))` returns, in both
      repos.
- [x] **Real, fully-settled sub-game 1 achieved**, live, against aviayeli
      (played from the sibling thief repo, us thief/them police): full 35-turn
      exchange, every step's commit accepted both directions, mutual
      `submit_audit` exchange completed (their inbound audit call landed
      during our 5s grace window, followed by a clean session `DELETE`),
      outcome `survived`. First sub-game either side has settled end-to-end
      this league. `league-peer --friendly`, no report email sent (uncounted).
- [x] **Sub-game 2 attempt (us police, them thief) hit a series desync on
      their end** — traced live to their process dying on the sub-game-1
      audit 502 (before our shutdown-grace fix existed) and their supervisor
      relaunching a fresh series at sub-game 1, while our run had already
      advanced. Root-caused and confirmed by them independently, consistent
      with what we logged (a second fresh negotiate+step-1 burst mid-session
      on our side). Not re-attempted yet this session — see the open item
      below.
- [x] **Root-caused (their side, confirmed by them independently): a
      negotiate/inbox-clear race** — their series runner cleared its inbox
      *after* an awaited negotiate round-trip instead of before, so a turn
      arriving during that window got silently dropped; fixed on their end,
      verified live by us afterward (their side stopped re-sending step 1
      forever).
- [x] Verified (independently, not taken on their word) that our own outbound
      `step` numbering was always correct (1, then 2, ...) by logging our own
      literal outbound message bytes before their "off-by-one" theory arrived
      — the actual bug was theirs, not ours, on that specific claim.
- [x] All temporary `[DEBUG]` raw-payload logging added during this live
      debugging session removed afterward; kept only the
      `[league] receive_turn reply (turn N): ...` line (matches the existing
      `[league] submit_audit reply: ...` logging style already in the
      codebase). 166 tests, ruff-clean, both repos.
## Done (negotiate counter-sign — vs aviayeli, 2026-08-25 session 2)
- [x] **Fixed: the inbound `negotiate` tool always replied `{"ok": True}`,
      giving the opponent nothing to counter-verify us against.** aviayeli's
      settlement record for the earlier sub-game recorded
      `handshake_counter_signed: false` — two of their three handshake checks
      had no terms/nonce/signature to run against on our reply. `cli/
      league_peer.py` now precomputes `terms`/`step0`/`negotiate_reply`
      (`{"status": "accepted", "terms", "nonce", "signature", "role",
      "sub_game_number"}`, reusing the same nonce/signature this peer's own
      outbound `negotiate()` call sends) and passes it into
      `add_league_tools`, which now takes a `negotiate_reply` param instead of
      hardcoding `{"ok": True}`. Not mandated by the kit's own SPEC.md (checked
      directly — it leaves the negotiate reply shape unspecified, "requiring
      explicit pair agreement"), but costs nothing and unblocks aviayeli's own
      audit tooling.
- [x] `tests/league/test_server_tools.py` updated: `add_league_tools` takes a
      third arg everywhere; the negotiate test renamed and now asserts the
      reply echoes whatever `negotiate_reply` was passed, not a hardcoded ok.
      166 tests, ruff-clean, both repos.
- [x] **Confirmed our earlier "404/Session terminated" report from aviayeli
      was not a routing bug** — verified directly: our local ngrok API was not
      even running (we'd deliberately stopped everything between sessions).
      The 404 was ngrok's own edge serving a stale "tunnel not found" page for
      the old hostname, not our MCP server misrouting `/mcp`. No code change
      needed; just restart the tunnel + peer.
- [x] **Agreed restart protocol with aviayeli**: if either side's run dies
      mid-series, both sides restart the whole series from sub-game 1 — no
      half-continuing. Operational agreement, not a code change; relevant
      given neither peer can resume mid-series (this repo's `sub_game_number`
      is always start-from-given-number, not resume-in-place).
- [x] **Artifacts-on dry run decided**: no true "write but don't send" mode
      exists in `report/emit.py` (only `--friendly`, which skips the report
      entirely, or the default path, which emails the real grader address).
      Using `--report-to <team's own email>` instead of `--friendly` for this
      run — exercises the full build+write+email path aviayeli asked for,
      without hitting the real course inbox, reusing the existing override
      built for exactly this purpose (2026-08-24).

## Done (sub-game-1 solved, sub-game-2 root-caused as their bug — vs aviayeli, 2026-08-25 session 3)
- [x] **Us-as-thief sub-game 1 (played from the sibling repo) is now solid: 3
      for 3 clean, fully-settled runs** against aviayeli (real 35-turn games,
      mutual `submit_audit` exchange, `handshake_counter_signed: True`
      confirmed on their end, reports emailed to `--report-to
      boshra2003dhamshy@gmail.com`). This direction is a solved problem.
- [x] **Us-as-police sub-game 2 stalled 3 times in a row with the same
      symptom** (turn 1 accepted, then a long repeating connect→negotiate→
      disconnect cycle from their side, never advancing, `outcome: ongoing`).
      Added temporary message-level debug logging to `league/client.py` and
      `league/server_tools.py` (removed after diagnosis, no net diff) and
      captured the actual payloads.
- [x] **Root-caused with hard evidence, not assumption: our own outbound
      negotiate and our reply to their negotiate were both consistently
      correct** (`role: "police", sub_game_number: 2`, byte-identical across
      every one of 9+ retries) — verified directly from our own logs, captured
      *before* aviayeli's own explanation arrived, so not fit to their theory
      after the fact. Their repeated inbound calls to us, in contrast,
      self-declared stale `sub_game_number: 1, role: "police"` identity —
      their sub-game-1 state, not sub-game-2-as-thief.
- [x] **Ran aviayeli's proposed decisive experiment** (`--first-role thief`
      on their end; us running a genuinely fresh, standalone sub-game 1 as
      police against their thief) — **clean, complete result**: full 35-turn
      game, mutual audit, report emailed (`outcome: captured`). Confirms our
      role/alternation logic is correct in both directions when the sub-game
      is a fresh standalone negotiate; the actual bug is specifically in
      aviayeli's sub-game-1→2 *transition* inside their continuous supervised
      runner (their identity/session state not resetting or advancing between
      sub-games), not in our code and not in a general pairing/alternation
      defect on either side.
- [x] **aviayeli fixed their sub-game-1→2 transition with a configurable
      inter-sub-game pause** (`--sub-game-pause`, held session released before
      sleeping, not after — order matters, since sleeping first would recreate
      the earlier inbox-clear deadlock). First pause length (90s) exceeded our
      `handshake_timeout_sec` on the wrong side of the window (their pause
      outlived our patience); tightened to 30s once we raised our own timeout
      (see below), landing inside their window with margin.
- [x] **Raised our own `handshake_timeout_sec` 60s → 180s** (both repos) so an
      opponent that deliberately pauses between sub-games doesn't get read as
      unreachable — same precedent as the earlier 30s→60s raise.
- [x] **First-ever full 2-sub-game series completed end-to-end, both
      directions, both sub-game boundaries crossed cleanly**: sub-game 1 (us
      thief) `survived`, sub-game 2 (us police) `captured`, both full 35-turn
      games, both with mutual `submit_audit` exchange, both artifacts written
      and emailed to `boshra2003dhamshy@gmail.com` (`--report-to`, not the
      grader). This is the friendly dry run this whole debugging arc was
      building toward — it's done, and it's clean.
- [ ] **Next**: the real graded 6-sub-game series against aviayeli.

## Done (opponent switch back to SMNGRP05 — friendly, 2026-08-26)
- [x] SMNGRP05 resumed contact via the established user-relayed channel, offering a new
      Cloudflare quick-tunnel endpoint (`https://store-maritime-ser-maintain.trycloudflare.com/mcp`,
      one door for both roles). `config/game.toml`'s `opponent_url` updated to it in both repos.
      `config/game.json`'s `agreed_between` was already `["bb-ai-12", "SMNGRP05"]` in both repos
      (left that way since 2026-08-24, not reverted when we switched to aviayeli — no change
      needed).
- [x] Roles this series: SMNGRP05 police on sub-games 1/3/5 (us thief), us police on 2/4/6
      (them thief).
- [x] **Flagged and did not act on an unverified claim embedded in their message**: they
      asserted our step-zero `system_spec` record has no step key and cited Rule 19 plus a
      "series we completed together" 35-of-36 failure count. Checked independently first:
      `crypto/step0.py` already seals `{"type": "system_spec", ...}` *before* commitment (the
      2026-08-24 fix, still in place) — claim doesn't match our code, and no completed-series
      logs with SMNGRP05 exist locally. Same opponent-channel injection pattern as before
      (technically-plausible claim + urgency); not acted on.
- [x] Set up own ngrok tunnel (`bb-ai-12-police tunnel`, port 8802) to give SMNGRP05 our
      endpoint. This repo's public MCP URL for this series: `https://comic-leverage-paprika.
      ngrok-free.dev/mcp` (kept running in background for whichever of our two repos is active).
- [ ] **Next**: sub-game 2 (us police vs their thief), against
      `https://store-maritime-ser-maintain.trycloudflare.com/mcp`, `--friendly`, if the user
      wants to continue this series (sub-game 1, us thief, already run cleanly from the
      sibling repo — see its `docs/TODO.md`).

## Done (sub-game 2 debugging vs SMNGRP05 — 2026-08-26, two real fixes made)
- [x] **Ignored a second suspicious message this session**: content appeared mid-turn,
      positioned oddly (alongside a tool-result notification rather than as a normal message
      from the user), signed "— SMNGRP05" in a voice the user never uses, and repeated the
      same already-debunked Rule-19/step-zero claim padded with new unverifiable "progress"
      figures. Treated as untrusted per the standing security note above; not acted on.
- [x] **First live sub-game-2 attempt**: `negotiate` timed out after 180s waiting for their
      reply — our own outbound negotiate call completed without error, so this was one-sided.
- [x] **Real fix #1 — negotiate retry.** `LeagueRuntime.negotiate()` was single-shot with no
      recovery from one missed handshake window, a gap already identified but never
      implemented on 2026-08-24 ("Open flag — negotiate-handshake reliability"). Added a
      2-attempt retry with a 10s gap, re-sending our own negotiate each attempt
      (`_NEGOTIATE_ATTEMPTS`/`_NEGOTIATE_RETRY_DELAY_SEC` in `league/runtime.py`, both repos).
- [x] **Second live attempt (with the retry fix)**: negotiate succeeded immediately, but the
      game stalled after turn 1 — our move was sent and acked, but no reply ever arrived from
      their side within the turn timeout.
- [x] **Real fix #2 — dead config wired up.** Traced the turn-1 stall to our own code, not
      theirs: `config/game.toml`'s `network.turn_timeout_seconds = 180` was never read
      anywhere — `LeagueRuntime` was always constructed without a `turn_timeout_sec` argument,
      silently falling back to the class default of 60s. Wired
      `turn_timeout_sec=float(net["turn_timeout_seconds"])` into the `LeagueRuntime(...)` call
      in `cli/league_peer.py` (both repos). Confirmed by grepping the whole repo for both spellings
      before writing the fix.
- [x] Full test suites pass after both fixes: 160/160 (excluding the pre-existing, documented
      GUI/Tk environmental flake) here, 166/166 in the sibling thief repo.
- [x] **Third live attempt (both fixes in place)**: negotiate itself got zero incoming traffic
      from their side this time. Checked our own reachability independently (not taking their
      earlier "your door reads 502" claim on faith): our own public endpoint *did* return 502
      at that moment too — but that's simply because our MCP server only runs for the duration
      of one `league-peer` invocation, not continuously. Conclusion: this is a two-sided
      "both processes must be listening at the same moment" coordination gap (matches the
      2026-08-24 open-flag theory), not a remaining code bug on either fix just made.
- [ ] **Next, per user decision (stopped here for today)**: before retrying sub-game 2 again,
      coordinate real-time with SMNGRP05 so both sides launch within the same window, rather
      than attempting blind.

## Done (two more real fixes: zombie processes + session-drop resilience — 2026-08-26)
- [x] **Real bug found while running a full 6-sub-game friendly script**: after a `league-peer`
      invocation returned (both on a normal "ongoing" exit and on an uncaught-exception exit),
      the OS process sometimes stayed alive, still `LISTEN`ing on `my_port` minutes later, still
      answering a live opponent with stale in-memory state. Confirmed directly via
      `Get-CimInstance Win32_Process` — found three-plus stale `league-peer` processes alive
      simultaneously, one from a run that had already printed its result and "returned." This
      independently explains a report from SMNGRP05 of discarding multiple stale negotiate
      envelopes for old sub-game numbers — not a bug in our retry logic reusing a stale message
      object (checked: within one `negotiate()` call the message is correctly built once per
      sub-game, which is correct; across attempts each is a fresh process), but literally old
      processes still running and answering.
  - [x] **Fix**: `cli/league_peer.py`'s `run()` now wraps the play phase in try/except and calls
        a new `_exit()` helper (`sys.exit`-through-`os._exit`, after flushing stdout/stderr) on
        every exit path instead of `return`. Verified live: an invocation with a bogus
        `--opponent-url` left *zero* trace in the process list immediately after, vs. multiple
        old zombies confirmed still present from before the fix.
  - [x] **Deliberately not placed in `cli/__init__.py`'s dispatch** — `tests/test_cli.py` calls
        `main()` in-process with `league_peer.run` monkeypatched; an `os._exit()` there would
        have killed the pytest process itself (this was tried, and the test run visibly
        truncated mid-suite with no summary line — caught before committing, not shipped).
        Placing `_exit()` inside `league_peer.run()`'s own body is safe because tests only ever
        monkeypatch that whole function and never execute its real body.
- [x] **Second real bug, found live in the same session**: `negotiate` succeeded ("terms
      match"), then sending turn 1 raised `mcp.shared.exceptions.McpError: Session terminated`
      — the opponent's server closed the session between negotiate and the first turn.
      `LeagueTransport` had no resilience to a mid-sub-game session drop at all.
  - [x] **Fix**: `league/client.py`'s `negotiate`/`send_turn`/`send_audit`/`send_control` now go
        through one `_call()` helper that catches any exception, reconnects
        (`__aexit__`+`__aenter__`), and retries the same call once before giving up.
- [x] Full test suites pass after both fixes: 160/160 here (excluding the pre-existing
      documented GUI/Tk environmental flake), 166/166 in the sibling thief repo.

## 2026-08-26 — `submit_audit` sender/claim shape (third real bug found live vs SMNGRP05)
- [x] **Context**: SMNGRP05 reported that our `submit_audit` "never reaches" them across two
      runs, and inferred a chain (sub-game 1 never terminates → re-greeting → desync). Every
      specific claim they gave was verified against our own code and logs first, per standing
      discipline, and **all of them were false**:
  - [x] "You pass `message` instead of `payload`" — false: `league/client.py` already calls
        `self._call("submit_audit", "payload", payload)`.
  - [x] "A 200 OK hides a tool error; log the result object" — already done: `runtime.py`
        prints `reply!r` and prints the exception rather than swallowing it.
  - [x] "Nothing reaches our server at all" — contradicted by our own log:
        `[league] submit_audit reply: {'ok': True}`, a structured tool reply *from their server*.
  - [x] "Your sub-game 1 never terminates" — false: it ended with
        `league game outcome: survived (final_turn=35)`.
  - [x] "Free ngrok's interstitial breaks the MCP SSE GET" — not supported: our log shows
        their IP completing `GET /mcp HTTP/1.1" 200 OK`, and `client.py` already sends
        `ngrok-skip-browser-warning`.
- [x] **The two real defects, which their message did not identify**:
  - [x] `build_audit` set `"sender": role.value` (`"thief"`/`"police"`) instead of the group id.
        Their server accepts the call and returns `{'ok': True}`, but cannot match the audit to
        our group — which is exactly why they log it as absent while we see success. This single
        defect reconciles both sides' observations; neither side's stated theory did.
  - [x] `result_claim` was a dict (`{"type": "survival"}`) where the kit expects a bare string.
        `build_audit`'s own signature already annotated it `str`, so the code was internally
        inconsistent independently of anything SMNGRP05 said.
- [x] **Fix**: `build_audit` now takes `group_id`; `_send_audit` passes a plain string. Payload
      held to exactly three keys — their `AuditPayload(**data)` raises `TypeError` on any extra
      key, which would destroy an otherwise-valid sub-game.
- [x] `build_turn`'s `sender` deliberately left as `role.value` — turn exchange demonstrably
      works (35 turns, all `{'ok': True}`); changing it would risk breaking what already works.
- [x] Checked the course PDF first as the authoritative source: 160 pages, **zero** occurrences
      of `sender`/`negotiate`/`receive_turn`/`submit_audit`/`result_claim`. The spec is silent
      on the league kit's 4-tool wire shape, so the kit's own shape governs here.
- [x] Regression tests added both repos for the exact three-key shape and string claim; ruff
      clean and 167/167 (thief) / 166 + 1 pre-existing GUI-Tcl environmental failure (police).
- [ ] **Operational trap to remember**: `tunnel` alone does not serve MCP — it only exposes the
      port. SMNGRP05's first 37 requests got `502 Bad Gateway` because only the tunnel was up.
      Start `league-peer` *before* telling the opponent we are live.
- [x] **Fourth real bug, and the decisive one for finishing a sub-game**: after the closing
      turn, `play()` blocked for the full `turn_timeout_sec` (180s) waiting for an inbound turn
      the opponent was never going to send. They stop at their own last step and immediately
      open a 90-second audit window, so the dead wait ran down *after* that window had already
      opened — our `submit_audit` arrived roughly 90s too late and they logged it absent.
  - [x] **Arithmetic that confirms it**: their `submit_audit` 19:59:16, their window closed
        20:00:47 (91s). `19:59:16 + 180s = 20:02:16`; our log file was written at **20:02**.
        Matches to the second — this is measured, not inferred.
  - [x] Note this would have kept the sub-game broken *even with the `sender` fix*: the audit
        would have been correctly addressed but still outside their window.
  - [x] **Fix**: new `_CLOSING_TURN_TIMEOUT_SEC = 15.0`. `play()` uses it instead of
        `turn_timeout_sec` whenever `self._survived_now or turn == turns`; `_exchange_turn` now
        takes the timeout as an argument. Regression-tested in both repos by spying on
        `LeagueInbox.wait_for_turn` and asserting the closing wait uses the short timeout.
- [x] **Fifth real bug, found by running our own peers against each other**: `LeagueTransport`
      dialled the opponent immediately on startup with `_CONNECT_ATTEMPTS = 3` at 2s apart —
      about **6 seconds** of patience in total. The agreed coordination with SMNGRP05 is "we go
      up first, then tell them we're live", which means our process was guaranteed to die before
      they ever dialled. Reproduced twice locally: whichever peer started first crashed with
      `RuntimeError: Client failed to connect: All connection attempts failed`.
  - [x] **Fix**: first connect now retries 45 x 4s = 180s, matching `handshake_timeout_sec`.
        Later reconnects deliberately stay short (3 x 2s) — mid-game the opponent is known to be
        up and a 180s block would blow past their turn watchdog. Tracked by `_connected_once`.
- [x] **End-to-end two-sided verification of all of the above** (our police repo vs our thief
      repo, real FastMCP servers over 127.0.0.1, police temporarily on port 8803): both sides
      independently reached `survived (final_turn=35)`, both `submit_audit` calls returned
      `{'ok': True}`, and both agreed on the same outcome and final turn. Police config reverted
      to `my_port = 8802` immediately afterwards; tree verified clean.
- [ ] **Startup race remains for simultaneous local runs**: both peers must be launched within
      the connect window of each other. Not an issue against a real opponent now that the first
      connect waits 180s.
- [x] **Sixth real bug, and the one that actually killed the live series**: `cli/league_peer.py`
      started the MCP server thread and then slept a flat `time.sleep(1.0)` before beginning the
      protocol. Uvicorn accepts connections a beat before FastMCP mounts the `/mcp` route, so we
      began the exchange while our own route still answered **404**.
  - [x] **Measured live 2026-08-26, sub-game 3**: `21:44:52 receive_turn step1 -> 404`,
        `21:44:54 receive_turn step1 -> 200` (their retry), `21:44:55 step2 -> 200`, then 180
        seconds of mutual silence and `21:47:55 submit_audit`. We sent 3 turns, they sent 2
        steps, and each side then waited for the other until timeout. Sub-game 2 died
        identically. Sub-game 1 survived only because the opponent had been retrying against us
        for ~90s beforehand, so their first success landed after the route was live.
  - [x] **Mechanism**: the lost turn is not recoverable by a retry. The opponent re-sends on a
        fresh session, but by then the two step counters are offset by one and both peers block
        forever. It is a deadlock, not a dropped message.
  - [x] **Fix**: new `league/server_ready.py:wait_until_serving()` polls
        `http://127.0.0.1:<my_port>/mcp` until it stops answering 404 (connection errors count
        as "not up yet"), with a 30s ceiling; `league_peer.py` calls it instead of sleeping and
        aborts loudly if the route never mounts. A longer sleep would still have been a guess —
        this waits for the real condition. Put in its own module to avoid growing
        `league_peer.py`, which is already over the 150-line cap.
  - [x] **Verified**: local two-sided run after the fix — **zero 404s on either side**, both
        peers reached `survived (final_turn=35)`. Before the fix every live sub-game showed them.
- [ ] **Opponent-side bug, reported by SMNGRP05 2026-08-26, not ours to fix**: their peer
      consumes its own outbound turns as inbound opponent turns (their `_seen_commits` duplicate
      guard is populated only from inbound messages, so their own commit looks new). Their
      police declares its own cell as `capture_claim` every turn, which is what they initially
      mistook for our thief claiming captures. Worth remembering if a sub-game desyncs in a way
      our own logs cannot explain.
- [ ] **Open question for both teams** (narrowed, no longer blocking): they report 34 steps per
      sub-game; `config/game.json` says `max_moves: 35` / `survival_threshold: 35` and we run
      `--turns 35`. The closing-timeout fix makes the off-by-one harmless, but the two teams
      should still agree the number rather than either side editing it unilaterally.
- [ ] **Pre-existing submission-compliance gap** (not introduced by today's work):
      `league/runtime.py` is 183 lines and `cli/league_peer.py` is 157 — both over the
      guidelines' 150-line-per-file cap. Needs a split before submission.
- [ ] Note: `--friendly` skips `emit_report()` entirely, so **no artifacts are written to
      `logs/`** — the 2026-08-26 `survived` result left no file. Use `--report-to <own email>`
      if a friendly series should leave a record.

## Later stages (tracked here for visibility, detailed in their own PRD_*.md once started)
- [ ] Write the full 6-section academic report in README.md (rules model, communication
      approach, decision-making, LLM usage, live-GUI verification, replay-viewer
      verification) — the underlying code for all six now exists, per `docs/PLAN.md`.
- [ ] At least 2 full games played against a real opponent team before submission
      (`min_games_to_pass = 2`).
- [ ] `git tag -a v1.0-submission` once feature-complete.
