# PRD — Stage 6: Security

## Goal
Add the cryptographic integrity layer the book requires: SHA-256 commit-reveal sealing for
every move, a Step-0 sealed hardware/software declaration, and a pre-game shared-config
agreement check. This stage is scoped tightly around what could be confirmed from the book
text already read this session — see "What's deliberately not built yet" below for the parts
that need a fresh re-read before implementation.

## Delivered
| Module | Responsibility | Book reference |
|---|---|---|
| `crypto/commit_reveal.py` | `canonical_json`, `generate_nonce` (`secrets.token_hex`), `compute_commitment`, `verify_reveal` — the core SHA-256 commit-reveal primitives; `SealedMove`/`CommitRevealLog` accumulate one sealed entry per turn and audit the whole sequence | Commit→Acknowledge→Reveal→Audit protocol, zero-knowledge framing |
| `crypto/step0.py` | `Step0Declaration` — seals `{team_code, python_version, platform, processor, machine}` via the same commit-reveal primitive | Step-0 signed hardware/software declaration |
| `shared/sysinfo.py` | `collect_sysinfo()` — the hardware/software fields Step-0 declares | — |
| `domain/negotiation.py` | `configs_match(local_sha256, remote_sha256)` — the pre-game shared-config agreement check | Appendix ב |
| `runtime/peer_runtime.py` | `run_turn_loop` now seals every outbound move via `CommitRevealLog.seal()` before sending it | FR-9 |
| `cli.py` | new `declare` subcommand — prints this peer's sealed Step-0 declaration as JSON | — |

## Design decisions
- **"Signed" means sealed via SHA-256 commit-reveal, not an asymmetric signature — a known,
  book-confirmed gap, not an assumption.** Direct book text (§5.5, p.39–40, read live
  2026-08-24): "המפרט כולו נארז למחרוזת JSON ונחתם קריפטוגרפית באמצעות מפתח המסופק מראש, כך
  שלא ניתן לזייפו בדיעבד" — "the entire spec is packed into a JSON string and cryptographically
  signed using a key supplied in advance, so it cannot be forged after the fact." This *does*
  describe a real pre-supplied signing key — a different, keyed mechanism from this module's
  unkeyed SHA-256 commit-reveal sealing. (An earlier draft of this note claimed the book "does
  not confirm" a signing scheme; that was written before the book was actually read this
  session and is now corrected.) No such key has been supplied to this project as of this
  writing; until one is (e.g. via a course announcement or the reference repo's own Step-0
  code — neither checked this session), this module's sealing is the most defensible
  substitute available, but it is a real, book-confirmed deviation, not a resolved question —
  see `docs/TODO.md`'s open flags.
- **The wire-level Commit→Acknowledge→Reveal message exchange is not implemented.** What's
  built is the *sealing and audit* machinery (`CommitRevealLog`) — a peer now locally commits
  to every move it sends, and can later prove none of its own sealed moves were tampered with
  after the fact. Actually exchanging commitments/acknowledgments/reveals *between* peers over
  the wire requires the same synchronized turn-taking protocol already deferred since stage 3
  (see `docs/PRD_strategy.md`) — building the crypto handshake on top of a turn protocol that
  doesn't exist yet would mean guessing at both simultaneously. This stage deliberately
  delivers the half that's independently testable and book-confirmed.
- **`domain/negotiation.py` is a check, not a handshake.** `configs_match` is the one negotiation
  primitive confirmed with confidence (byte-identical `config/game.json`, verified via
  SHA-256 — `ConfigManager.game_json_sha256()` already existed from stage 1). The rest of a
  real negotiation handshake (game_id assignment, who moves first) stays an open item pending
  a fresh read of the book's exact protocol text.

## Acceptance criteria (all met)
- [x] `canonical_json` sorts keys and strips whitespace (`{"b":1,"a":2}` → `'{"a":2,"b":1}'`).
- [x] `compute_commitment`/`verify_reveal` round-trip correctly; a tampered payload fails
      verification.
- [x] `CommitRevealLog.audit()` returns `True` for an untouched log and `False` — with the
      exact tampered turn numbers from `tampered_turns()` — after a payload is mutated
      post-hoc (simulating a corrupted log, the same failure mode the stage-7 Replay Viewer
      will need to detect).
- [x] `Step0Declaration.create` seals real `sysinfo` output; `.verify()` is `True` until the
      payload is tampered with, then `False`.
- [x] `PeerRuntime.run_turn_loop` seals every move it sends; `commit_log.audit()` passes after
      a full run.
- [x] `bb-ai-12-police declare` (and the thief equivalent) run for real and print a valid
      sealed declaration with `verify() = True` — manually confirmed, not just unit-tested.
- [x] `uv run pytest -q --cov=src` passes at 92% coverage (74 tests); `uv run ruff check .` is
      clean.

## Addendum — 2026-08-20 book re-verification
The book PDF turned out to be locally readable on this machine. Re-reading ch.5.3 directly
(full `commit()`/`verify()` code sample) found a real bug: `compute_commitment` was hashing
`canonical_json(payload) + nonce` as two concatenated strings, but the book's exact formula is
`Hcommit = SHA256(canonical_json({...payload, "nonce": nonce}))` — the nonce belongs *inside*
the single canonically-serialized record. Fixed in both repos; a new test
(`test_compute_commitment_matches_the_books_exact_formula`) pins the corrected formula
byte-for-byte. Also added `runtime/state_machine.py`'s `GamePhaseMachine`, reproduced from the
book's own ch.8.3 example code (`WAITING_FOR_OPPONENT → COMPUTING_MOVE → COMMITTING →
AWAITING_REVEAL → VERIFYING`, with `TECHNICAL_LOSS` as a terminal error state) — not yet wired
into `PeerRuntime`, since doing so properly requires the wire-level protocol redesign already
described below, and one open question the book text read this session didn't settle: whether
a "turn" is strict alternation or a simultaneous joint round (see `docs/TODO.md`).

## Explicitly deferred to later stages
- Real synchronized turn-taking / negotiation handshake (`peer/turn_handler.py`,
  `peer/handshake.py`) — still open since stage 3, now also blocking the wire-level
  commit-reveal exchange described above. Re-check the book's exact protocol text first.
- Barrier-aware routing, deceptive hints, pheromone spatial spread — still open from earlier
  stages (see `docs/TODO.md`).
- Live ngrok tunnel — the user's own action on match day (stage 5).
- Gmail reporting (which will consume `CommitRevealLog`/`Step0Declaration` to build the four
  mandatory JSON artifacts), GUI, replay viewer (which will reuse `CommitRevealLog.audit()`
  for its "Verified OK"/"TAMPERED" banner) — stage 7.
