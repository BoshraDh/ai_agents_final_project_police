# PRD — Automatic End-of-Game Detection (closes the stage-7 deferred item)

## Goal
Replace `PeerRuntime.run_turn_loop`'s previous behavior — always running exactly the
requested `--turns N`, with no awareness of the actual game rules — with automatic
capture/survival detection, so a real match stops the instant the sub-game is actually over
instead of running past it (or requiring a human to eyeball the printed positions each round).

## What this reuses vs. what's new
No new detection *logic* was needed: `domain.rules.outcome_after_step` (built in stage 1,
tested since) is already the single source of truth for "is the sub-game over, and how." The
only new piece is `domain.rules.cop_and_thief_positions(role, own_position, opponent_position)`
— a small, pure mapping function that translates a peer's role-relative `BeliefState`
(`own_position`/`opponent_position`, which is symmetric between cop and thief) into the rules
layer's role-neutral `(cop_pos, thief_pos)` argument order that `outcome_after_step` expects.

## Delivered
| Module | Responsibility |
|---|---|
| `domain/rules.py` | `cop_and_thief_positions` — pure role→(cop,thief) position mapper |
| `runtime/peer_runtime.py` | `PeerRuntime` gains `role: Role`, `survival_threshold: int` constructor params, `self.outcome`/`self.final_turn` state, and `_check_outcome(turn)`; `run_turn_loop` calls it after every round and breaks with a `GAME OVER` print (including both sides' scores via `domain.scoring.scores_for_both`) the moment the outcome leaves `ONGOING` |
| `cli/` (was `cli.py`) | Split into a package (`__init__.py`, `check_config.py`, `peer.py`, `tunnel.py`, `declare.py`, `replay.py`) — the flat file hit the 150-line cap once `role=Role.POLICE` and `survival_threshold=...` were added to `peer`'s `PeerRuntime` call |

## Design decisions
- **No extra coordination message needed.** Both peers independently compute
  `outcome_after_step` from the *same* round's honestly-relayed positions (the P2P
  zero-shared-state design already guarantees each side's `BeliefState` reflects exactly what
  the other side revealed that round), so both sides reach the same CAPTURED/SURVIVED
  conclusion on their own, without asking each other "are we done yet?" This is a direct,
  pleasant consequence of the honest-relay assumption already in place since the base-logic
  stage, not something new that had to be built.
- **`_check_outcome` runs after belief/scent updates, not before.** The check uses
  `self.belief.own_position`/`self.belief.opponent_position` *after* both `apply_own_move` and
  `apply_opponent_move` have run for that round — i.e. it checks the state that actually
  resulted from the round just played, matching the book's "after a step" framing for
  `outcome_after_step`.
- **`TECHNICAL_LOSS` and `self.outcome` remain two separate, non-overlapping concerns.** A
  network failure still only moves `self.machine.state` (the protocol phase) to
  `TECHNICAL_LOSS` and re-raises, unchanged from the prior turn-protocol stage; it does *not*
  set `self.outcome`, since a technical loss is a protocol-layer failure, not a game-rules
  outcome. This asymmetry is accepted as-is — this feature was specifically about *game*
  end-detection (capture/survival), not network-failure handling.
- **`survival_threshold` and `role` are both passed in from the caller** (`cli/peer.py`, in
  turn reading `config/game.json`'s `movement_and_barriers.survival_threshold` and hardcoding
  `Role.POLICE`/`Role.THIEF` per repo) rather than re-derived inside `PeerRuntime`, matching
  the existing pattern where all game-rule constants come from config, never hardcoded in the
  runtime layer (NFR-4).

## Acceptance criteria
- [x] `cop_and_thief_positions` correctly maps both roles (2 new unit tests, both repos).
- [x] `run_turn_loop` stops after exactly the round capture happens, not after the full
      `--turns` count (`test_run_turn_loop_stops_early_on_capture`).
- [x] `run_turn_loop` stops after exactly the round `survival_threshold` is reached
      (`test_run_turn_loop_stops_early_on_survival`).
- [x] `run_turn_loop` stays `ONGOING` (no early stop, `final_turn` stays `None`) when the
      requested `--turns` cap is reached before either win condition
      (`test_run_turn_loop_stays_ongoing_when_the_cap_is_reached_first`).
- [x] 122 tests, 93% coverage (police) / 122 tests, 92% coverage (thief), both ruff-clean.
- [ ] **Live two-process verification — attempted, blocked by an unrelated pre-existing bug**
      (see below), not by anything in this feature. Verification instead relies on the unit
      tests above, which directly exercise `run_turn_loop`'s early-stop logic through a
      stubbed transport — the same code path a real run would take, minus the live networking
      layer where the blocking bug actually lives.

## A real bug found while attempting live verification (fixed same day — see `docs/TODO.md`)
Two independent, freshly-started `peer` processes (as a real match against another team
necessarily involves — no shared start signal between two different teams' machines) reliably
failed on round 1: whichever peer's `send_reveal` call reached the opponent's `submit_reveal`
handler before that opponent had locally finished its own `TurnHandler.prepare_own_reveal` for
the same round got a hard `ValueError`, crashing that side. Root cause: the book's protocol
calls for an **Acknowledge** step that should "ensure reveal only after both sides have
committed" — this repo's wire protocol never actually waited for that; each side sent its
commit and immediately called the opponent's `submit_reveal`, which only succeeded if the
opponent happened to have already raced ahead locally. This was pre-existing in the turn
protocol built in the previous stage (`docs/PRD_turn_protocol.md`), not something this
feature introduced, and reproduced 100% of the time across 2 separate attempts. **Fixed the
same day**: `TurnHandler.wait_for_own_reveal` makes an inbound `submit_reveal` block until this
peer's own reveal is locally ready instead of failing immediately. See `docs/TODO.md`'s "Done
(commit-reveal round-1 race — fixed, 2026-08-20)" entry and `docs/PRD_turn_protocol.md`'s
"Update — 2026-08-20" section for full detail, including the re-run live verification.

## Explicitly still deferred
- The `send-report` CLI command itself (build the four JSON artifacts and email them
  automatically once `PeerRuntime.outcome` leaves `ONGOING`) — this feature only makes that
  meaningful to build; it isn't built yet.
- ~~The pre-existing "benign teardown race"~~ — also fixed same day: `cli/peer.py` now
  waits `_SHUTDOWN_GRACE_SEC` before exiting once the outcome leaves `ONGOING`. See
  `docs/TODO.md`'s "Done (benign teardown race — fixed, 2026-08-20)" entry.
- Everything already deferred from the turn-protocol stage (barrier placement, deceptive
  hints, real negotiation handshake, mutual end-of-game audit exchange, pheromone spatial
  spread, live ngrok tunnel).
