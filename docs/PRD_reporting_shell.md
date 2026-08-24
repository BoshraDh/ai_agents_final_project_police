# PRD — Stage 7: Reporting Shell

## Goal
The final book-mandated layer: build the four standardized JSON report artifacts, email them
to the grader via the Gmail API behind a rate-limiting Gatekeeper, and give the human a
local-truth-only live view plus an audit-reusing replay viewer.

## Delivered
| Module | Responsibility |
|---|---|
| `domain/game_ids.py` | `generate_game_id`, `artifact_filename` — id + filename scheme for the four artifacts |
| `report/artifacts.py` | `build_declaration/config/log/result` — four pure builder functions producing the exact JSON dicts |
| `report/report_writer.py` | `write_artifacts` — writes the four files to `logs/<group_id>/` |
| `shared/api_gatekeeper.py` | `TokenBucketGatekeeper` + `run_guarded` — token-bucket rate limiter + concurrency cap + retry/backoff, from the `rate_limiter_gatekeeper` config block |
| `infra/email_sender.py` | `build_message`, `send_report` — Gmail API `messages.send` body builder + wrapper, `gmail.send` scope only |
| `gui/live_gui.py` | `LiveGui` — Tkinter grid canvas + turn banner, draws only this peer's own `BeliefState` (never an omniscient board) |
| `gui/replay_viewer.py` | `ReplayViewer`, `load_log`, `verify_move` — step-through viewer that re-verifies every move's SHA-256 commitment and shows "Verified OK"/"TAMPERED" |
| `cli.py` | new `replay --log <path>` subcommand — opens the real Tkinter replay viewer on a saved log file |
| `crypto/commit_reveal.py` | `CommitRevealLog.entries()` — new read-only accessor so the report layer can build the `log` artifact from a completed game's sealed moves |

## Design decisions
- **Gmail OAuth2 credential setup is a live, guided step.** `infra/email_sender.py` only
  *consumes* an existing `token.json`; it never tries to create a Google Cloud project, enable
  the Gmail API, or run the browser consent flow itself. Per the user's own explicit request
  earlier in this project ("if you need me to install/download anything... guide me and tell
  me 'okay'"), that flow was walked through live, step by step, with her — see "Live setup
  walkthrough" below, now marked complete with the real outcome.
- **Update — 2026-08-24: `report/emit.py` now exists and is wired in.** Both blockers above
  are resolved: `PeerRuntime`/`LeagueRuntime` now detect capture/survival and stop with a real
  `GameOutcome` (see `docs/PRD_end_of_game_detection.md`), so `emit_report(...)` — build all
  four artifacts, write them, email them via `send_report` under the Gatekeeper — has a real
  outcome to report. `cli/peer.py` and `cli/league_peer.py` both call it once their run leaves
  `ONGOING`. A failed send is logged and swallowed, not fatal, since the artifacts are already
  safely on disk by then. See `docs/TODO.md`'s "Done (automatic send-report hook)" for the
  exact wiring and `tests/report/test_emit.py` for the send-succeeds/send-fails coverage.
  **Not yet proven with a real live send from inside a real match** — the next real game
  played will be the first live end-to-end proof of this hook specifically.
- **The Gatekeeper's `queue_depth` is stored/validated but no bounded queue is built.** A
  single caller (one email, once, per finished game) never needs a real queue; `run_guarded`'s
  retry-with-backoff already covers the realistic case of a transient 429 from Gmail.
- **The live GUI stays local-truth-only**, per the book's explicit rule — it renders
  `BeliefState`, never a global board, even though `BeliefState` happens to be exact right now
  (see the stage-3/4 notes on why that's still honest, not a loophole).

## Live setup walkthrough — completed 2026-08-20
Done live with the user, step by step, one confirmation at a time:
1. Created a Google Cloud project (`bb-ai-12-police-thief`).
2. Enabled the Gmail API.
3. Configured the OAuth consent screen (External, added her own address as a test user —
   the first attempt failed with `access_denied: 403` because that step was missed initially;
   fixed by adding the test user under Audience and retrying).
4. Created an OAuth client (Desktop app type), downloaded the client secret JSON, saved as
   `credentials.json` in both repo roots (gitignored, never committed).
5. Ran a one-time local script (`InstalledAppFlow.from_client_secrets_file(...)
   .run_local_server()`) — opened her browser, she signed in and granted `gmail.send`; wrote
   `token.json` (gitignored) with a `refresh_token`, so no further login is needed unless it's
   revoked. Copied the same `token.json` into the thief repo too (same Google account covers
   both peers for now).
6. **Verified with a real send**: `infra.email_sender.send_report` sent an actual email via
   the live Gmail API to `rmisegal+uoh26finalgame@gmail.com` (subject clearly marked as a
   setup test, no real attachments), and Gmail returned a real message id. The one-time setup
   script was deleted after use — `email_sender.py` is the only code that touches Gmail going
   forward.

## Acceptance criteria (all met)
- [x] `build_declaration`/`build_config`/`build_log`/`build_result` produce correct dicts,
      including a tampered-log case where `audit_passed` correctly flips to `False`.
- [x] `write_artifacts` writes all four files with the exact book-mandated naming pattern
      (`declaration_<id>.json`, `config_<id>_g<NN>.json`, `log_<id>_g<NN>.json`,
      `result_<id>.json`) to `logs/<group_id>/`.
- [x] `TokenBucketGatekeeper`/`run_guarded` are fully deterministic under test (explicit `now`
      injection, fake `sleep`) — acquire/release/concurrency-cap/retry-then-raise all covered.
- [x] `build_message`/`send_report` are fully testable without any real Google credentials or
      network call, via an injected `service_factory`; the MIME message correctly attaches
      JSON files under their original filenames.
- [x] `LiveGui`/`ReplayViewer` construct, render, and close without exceptions (smoke-tested
      with `show=False`); `ReplayViewer.next_move` correctly stops at the last entry.
- [x] **Manually verified the full pipeline end-to-end, for real, on disk**: created a real
      `Step0Declaration`, sealed real moves into a `CommitRevealLog`, built all four artifacts,
      wrote them to `logs/bb-ai-12/`, reloaded the log file from disk with `load_log`,
      re-verified every move (`True`/`True`), then tampered with a reloaded move's payload and
      confirmed `verify_move` correctly flips to `False` — this is exactly the check the
      Replay Viewer performs, run for real against real files, not just in a unit test.
- [x] `uv run pytest -q --cov=src` passes at 93% coverage (100 tests); `uv run ruff check .`
      is clean.
- [x] **Live Gmail OAuth setup completed and verified with a real send** — see "Live setup
      walkthrough" above.

## Explicitly deferred
- ~~A `send-report`/full game-completion CLI command~~ — **built 2026-08-24**, see the design
  decisions above and `docs/TODO.md`.
- Real synchronized turn-taking, barrier placement, deceptive hints, pheromone spatial spread,
  live ngrok tunnel — all still open from earlier stages (see `docs/TODO.md`).
- `cli.py` is now 145 lines — close to the 150-line cap. The next subcommand added will need
  the CLI split across multiple files (e.g. a `cli/` package with one module per subcommand).
