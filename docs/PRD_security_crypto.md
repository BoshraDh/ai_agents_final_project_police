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
- **"Signed" means sealed via SHA-256 commit-reveal, not an asymmetric signature.** The book
  text confirmed this session specifies SHA-256, canonical JSON, and `secrets.token_hex`
  nonces — it does not confirm a public-key signing scheme (RSA/Ed25519/etc.) for Step-0. This
  module therefore does not invent one. If the book specifies real signatures elsewhere, that
  needs revisiting before a real submission — logged in `docs/TODO.md`, not silently assumed.
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
