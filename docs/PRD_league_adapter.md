# PRD — League Kit Protocol Adapter (2026-08-24)

## Goal
Play real matches against opponents (SMNGRP05 and others in this league) that run the
`copthief-league-protocol` kit's 4-tool wire shape (`negotiate`/`receive_turn`/`submit_audit`/
`receive_control`) instead of this repo's own `submit_commit`/`submit_reveal` protocol. Built
as an **alternate, opt-in transport** (`league-peer` CLI command) — the existing `peer` command
and its wire protocol are unchanged for every other opponent.

## Why this needed a real design, not just 4 wrapper tools
SMNGRP05 initially proposed thin adapter tools that call our existing `submit_commit`/
`submit_reveal` internally. That doesn't work: their protocol never discloses a move mid-game
— only `hint` + `smell_grid` (a probabilistic scent field) + an opaque `commit` hash — with the
real move only appearing once, in `submit_audit`'s batched `records`, at game end. Our own
`HeuristicBrain`-based strategy needs *some* position estimate every round to chase/evade, so
this repo now feeds it a best-guess position derived from the opponent's `smell_grid`
(`league/smell.py`'s `guess_position_from_smell` — the strongest-scented cell) instead of the
exact tracked position `PeerRuntime`/`BeliefState` uses for every other opponent.

Capture detection is also fundamentally different: instead of position equality, the kit uses
an explicit, real-time `capture_claim`/`claim_response` exchange (police declares its own true
cell every round; thief must truthfully confirm/deny occupying it the following round) — which
independently matches book rules 46/47 found while cross-checking the book this session.
Survival is self-declared by the thief via `win_claim` once its own step count reaches
`survival_threshold`.

## Delivered
| Module | Responsibility |
|---|---|
| `league/terms.py` | Translates `config/game.json` into the kit's 14-key canonical wire form; builds/verifies the `negotiate` signature. Verified byte-for-byte against SMNGRP05's own example string. |
| `league/smell.py` | Bridges `PheromoneField` ↔ the kit's `{"r,c": intensity}` wire shape; `guess_position_from_smell` feeds the unmodified `HeuristicBrain` a best-guess target. |
| `league/inbox.py` | Buffers inbound `negotiate`/`receive_turn`/`submit_audit` messages for the (separate-thread) game loop to poll — same blocking-wait pattern as `peer/turn_handler.py`'s `wait_for_own_reveal`. Negotiations are keyed by **sub-game** (the terms are identical across all six, so a stale greeting would otherwise validate), and `reset_turns()` drops anything buffered before the handshake — turns carry no sub-game number, so arrival time is the only filter available. |
| `league/server_ready.py` | `wait_until_serving()` — polls our own `/mcp` until it stops answering 404, so we never begin the exchange while our own route is unmounted. Uvicorn binds a beat before FastMCP mounts the route; the opponent's reply landing in that gap offsets both step counters and deadlocks the sub-game. |
| `league/server_tools.py` | Registers the 4 inbound tools on the existing FastMCP server, alongside (not replacing) `submit_commit`/`submit_reveal`. |
| `league/client.py` | `LeagueTransport` — one persistent `Client` session per sub-game (not per call), per the kit's own guidance about free-tier tunnel rate limits. |
| `league/messages.py` | Pure builders for the exact wire shapes SMNGRP05 specified, including the `submit_audit` record-0 `system_spec` entry and the `payload`/`message` argument-name asymmetry. `build_audit` takes the **group id** (not the role) as `sender`, and `result_claim` is a bare string — exactly three keys, no more. |
| `league/outcome.py` | Pure capture/survival detection from one inbound turn message — kept separate from `runtime.py` to stay under the 150-line cap. |
| `league/runtime.py` | `LeagueRuntime` — the actual game loop: negotiate once, then per round decide → seal → build+send the turn message → wait for the opponent's → update the smell-based guess → check outcome. |
| `cli/league_peer.py` | New CLI subcommand (`bb-ai-12-police league-peer --turns N --opponent-url URL`), a peer to `cli/peer.py` for this alternate protocol. |

## Verified
- **`to_wire_terms` output matches SMNGRP05's exact canonical string byte-for-byte** — the
  handshake's exact-dict-equality gate will pass.
- **A real two-sided smoke test** (both repos' actual `LeagueRuntime`/`PoliceBrain`/`ThiefBrain`,
  real local FastMCP servers, real network calls over `127.0.0.1`, not mocks) completed a full
  `negotiate → per-round exchange → win_claim → submit_audit` cycle: both sides independently
  agreed the terms matched, and both independently arrived at the identical outcome
  (`survived`) at the identical `final_turn` — proving the protocol is genuinely symmetric and
  correct, not just that one side's code runs.
- 157/158 tests (police/thief), 91% coverage both, ruff-clean both.
- **`submit_audit` sender/claim shape corrected 2026-08-26.** SMNGRP05 reported our audit never
  arriving; independent verification showed their stated causes were all wrong (we already pass
  the `payload` argument name, already log the tool result object rather than the HTTP status,
  and our sub-game 1 terminated normally with `survived (final_turn=35)` after their server
  returned `{'ok': True}` to our audit). The real defects were that `sender` carried
  `role.value` instead of the group id — so their server accepted the call but could not match
  the audit to us — and that `result_claim` was a dict where the kit expects a string. Both
  fixed; regression-tested for the exact three-key shape.

## Explicitly out of scope / simplified
- **Barrier placement and barrier-based capture** (`barrier_placed` field) — this repo's
  `PoliceBrain` doesn't decide barrier placement at all yet (a pre-existing gap, not new here).
- **`receive_control`** is a pure no-op ack — no pause/resume/restart handling.
- **Negotiate validation is best-effort, not enforced**: `LeagueRuntime.negotiate()` returns
  whether the terms/signature matched, but `play()` doesn't currently refuse to proceed on a
  mismatch — acceptable for a friendly, worth hardening before a counted series.
- **No mutual mid-game trust beyond the claim exchange**: this repo doesn't independently
  verify the opponent's `submit_audit` records against their earlier commits (i.e., doesn't
  replay the kit's own `verify_vectors.py`-style audit check on what we receive) — we trust our
  own locally-observed `capture_claim`/`claim_response`/`win_claim` outcome, not a full replay
  of the opponent's sealed history.
- This adapter's commit-reveal primitive reuses `crypto/commit_reveal.py`'s already-switched
  league-kit formula (see `docs/TODO.md`'s 2026-08-24 entry) — no separate formula needed here.
