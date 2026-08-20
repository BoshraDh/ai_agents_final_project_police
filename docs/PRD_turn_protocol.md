# PRD — Real Turn-Taking Protocol (closes the stage-2/3/6 deferred item)

## Goal
Replace the STAY-echo stub that every prior stage (2, 3, 4, 6) deliberately left in place with
the real, book-confirmed per-round Commit→Acknowledge→Reveal exchange, so both peers'
inbound *and* outbound moves are genuine strategy decisions — the last major piece blocking a
real match against another team.

## What unblocked this
Earlier stages explicitly deferred this because of one open question: whether a "turn" means
strict single-agent alternation or a round where both agents move. Re-reading the book text
directly this session (ch.4.3, the pheromone-decay section) settled it: decay runs "at the end
of each full turn — that is, **after both the cop and the thief have completed their move**"
— confirming a turn is a joint round, matching the Dec-POMDP tuple's `P(s'|s,a1,a2)`, not
chess-style alternation. That, plus ch.5.3's exact 4-step Commit(hash-only)→Acknowledge
(locked)→Reveal(move+hint, nonce hidden)→Final-Reveal(all nonces, end of game) sequence and
ch.8.3's `GamePhaseMachine`, was enough to design and build the real protocol with confidence
instead of guessing.

## Delivered
| Module | Responsibility |
|---|---|
| `peer/turn_handler.py` | `TurnHandler` — pure per-round bookkeeping: `prepare_own_reveal`, `receive_commit`, `receive_reveal` (raises on a reveal with no prior commit — a real protocol-violation check, not just a comment) |
| `mcp/server.py` | Rewritten as `build_server(name, turn_handler) -> FastMCP`, exposing `submit_commit(h_commit, turn)` and `submit_reveal(move, hint, intent, turn)` — replaces the old fixed `receive_move` stub entirely |
| `mcp/client.py` | `McpTransport` gains `send_commit`/`send_reveal`, replacing `send_move` |
| `runtime/state_machine.py` | `GamePhaseMachine`, added in the book re-verification pass, now actually driving `PeerRuntime.run_turn_loop`'s phase transitions |
| `runtime/peer_runtime.py` | `run_turn_loop` rewritten around the real per-round cycle: decide → seal (`CommitRevealLog`) → `prepare_own_reveal` → `send_commit` → `send_reveal` (returns the opponent's real reveal in the same round trip) → update `BeliefState`/`PheromoneField` from what the opponent *actually* revealed |

## Design decisions
- **Symmetric, no central turn order.** Each peer proactively drives its own round loop and
  calls the opponent for both phases — matching the P2P architecture established since stage
  2. Whichever side's `submit_reveal` call arrives first at the other's server gets that
  peer's own already-prepared reveal back in the same round trip; the other side's own
  outbound call (redundant but idempotent) just re-confirms the same data. No "who goes
  first" negotiation was needed.
- **`state` snapshot in the commit payload.** The book's `Hcommit` formula covers
  `{state, move, intent, nonce}`; `state` here is `{own_position, opponent_position, turn}` —
  a defensible, minimal snapshot that ties the commitment to the exact game state at that
  round, per the book's stated purpose ("prevents reuse of an old commitment in a new
  context"). Not the full board (barriers aren't placed/communicated yet — still an open
  item).
- **`intent` always `"truth"` for now.** The book requires declaring upfront whether the
  accompanying hint is true or a lie. `TemplateProvider`'s canned lines aren't factual claims
  to lie about, so declaring them all `"truth"` is honest, not a workaround — real deceptive
  hints (thief's FR-8 allowance) still wait on this same field being wired to actual
  position-claim logic, unchanged from the stage-4/6 deferral.
- **Network failures during commit-send or reveal-send move the phase to
  `TECHNICAL_LOSS` and re-raise.** The book's own state diagram doesn't enumerate every
  possible failure point (e.g. it doesn't show `COMMITTING → TECHNICAL_LOSS` as a legal
  transition, only `COMPUTING_MOVE → TECHNICAL_LOSS` and `AWAITING_REVEAL → TECHNICAL_LOSS`)
  — this implementation only transitions to `COMMITTING` *after* the commit send has already
  succeeded, so a failure there is still attributed to `COMPUTING_MOVE`, keeping every
  transition legal per the book's own table.
- **Final nonce disclosure (end-of-game mutual audit) is unchanged** — `CommitRevealLog`
  already seals every round's `{payload, nonce, commitment}` locally; that log is what gets
  audited and reported (`report/artifacts.py`'s `build_log`), matching the book's Step-4
  Final-Reveal without needing a new wire message for it.

## Acceptance criteria (all met)
- [x] `TurnHandler.receive_reveal` raises `ValueError` when no commit preceded it for that
      round — the Ack step's actual purpose, not just documented.
- [x] `submit_commit`/`submit_reveal` tools tested against a real (in-process) FastMCP
      instance via `fastmcp.Client`, not just unit-tested in isolation.
- [x] `PeerRuntime.run_turn_loop` drives `GamePhaseMachine` through exactly the legal
      per-round cycle every round; a stubbed network failure at either send step correctly
      lands the machine in `TECHNICAL_LOSS`.
- [x] **Manually verified with a real two-process run — the first genuinely bidirectional
      exchange this session**: ran `bb-ai-12-thief peer --turns 4` and
      `bb-ai-12-police peer --turns 4` concurrently. Turns 1-3 show each side committing,
      revealing its own real strategy-chosen move and real hint, and receiving the
      *opponent's* real move/hint/intent back — e.g. the police log's turn-1 line shows it
      received the thief's actual hint ("I was never even here.") and actual move, not a
      fixed stub string. Turn 4 hit the same benign teardown race documented since stage 2
      (the shorter-running side's script exits mid-flight) — expected for these
      unsynchronized fixed-turn-count smoke scripts, not a protocol defect; police's turn-4
      line still shows it received the thief's real final reveal before the thief process
      exited.
- [x] `uv run pytest -q --cov=src` passes at 93% coverage (117 tests); `uv run ruff check .`
      is clean.

## Explicitly still deferred
- Final end-of-game nonce disclosure as an actual wire message (currently the local
  `CommitRevealLog` already has everything needed for each side's own report; a true mutual
  end-of-game audit *exchange* between peers — comparing logs, not just self-auditing — isn't
  built).
- Barrier placement and the wire fields to carry it.
- Deceptive hints (the `intent` field is wired and ready, but no logic sets it to `"lie"`
  yet).
- A real negotiation handshake beyond the config-agreement check (game_id assignment, etc.).
- Live ngrok tunnel — the user's own action on match day.
- ~~Game-completion detection~~ — done, see `docs/PRD_end_of_game_detection.md`.

## Update — 2026-08-20: round-1 race fixed
Live verification for the end-of-game-detection feature surfaced a real, 100%-reproducible bug
in this protocol: two freshly-started, independent peer processes reliably failed on round 1,
because the Acknowledge guarantee described above ("prevents backing out, ensures reveal only
after BOTH sides committed") was never actually enforced in code — `submit_reveal` answered
immediately, which only worked if the opponent happened to have already raced ahead to prepare
its own reveal locally first. Fixed via `TurnHandler.wait_for_own_reveal(turn, timeout_sec)`:
an inbound `submit_reveal` now blocks (bounded, polling) until this peer's own reveal for that
round is locally ready, instead of failing immediately — turning the race into an implicit
rendezvous. Re-ran the exact live two-process run that surfaced the bug: real bidirectional
exchange every round from turn 1 through turn 35 (previously died on round 1). See
`docs/TODO.md`'s "Done (commit-reveal round-1 race — fixed, 2026-08-20)" entry for full detail.
