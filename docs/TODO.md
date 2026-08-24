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
- [ ] **Step-0 "signing" key** — book ch.5.5 mentions signing with "a key supplied in
      advance"; no such key has been issued/found yet. Revisit if/when one is supplied (e.g.
      in a course announcement or the reference repo's own Step-0 code), and treat the current
      SHA-256-commit-reveal-based sealing as a placeholder until then.
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

## Open flag — reconcile before final submission
- [ ] **This repo's commit-reveal formula no longer matches the book's ch.5.3 literal code
      sample.** If book-formula compliance turns out to matter more for grading than being
      able to complete a real match, this is a one-function revert (see git history /
      the module docstring's "before" formula) — not a design dead-end, a live, reversible
      trade-off made under time pressure the night before a deadline.

## Later stages (tracked here for visibility, detailed in their own PRD_*.md once started)
- [ ] Write the full 6-section academic report in README.md (rules model, communication
      approach, decision-making, LLM usage, live-GUI verification, replay-viewer
      verification) — the underlying code for all six now exists, per `docs/PLAN.md`.
- [ ] At least 2 full games played against a real opponent team before submission
      (`min_games_to_pass = 2`).
- [ ] `git tag -a v1.0-submission` once feature-complete.
