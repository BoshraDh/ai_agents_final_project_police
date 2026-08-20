# PRD — bb-ai-12 Police Peer

## Purpose
A fully decentralized, peer-to-peer AI agent that plays the "police" role in the
Police-Thief pursuit game defined by `police_thief_p2p.pdf` v3.0.0, against an
independently-developed "thief" agent (sibling repo: `bb-ai-12-thief`), with no central
server, no shared memory, and no referee.

## Functional requirements

- **FR-1 Board & movement**: play on a `grid_size x grid_size` grid (book minimum 7x7),
  4-orthogonal + STAY movement, no diagonals, no illegal off-board or barrier-blocked moves.
- **FR-2 Barriers**: police may place up to `max_barriers` barriers, only adjacent to its own
  current position, irrevocably, honestly declared (no hidden placement).
- **FR-3 Capture**: police wins a sub-game by landing on the thief's true cell and issuing an
  honest `capture_claim`; a false claim is caught by the crypto audit (stage 6) and forfeits.
- **FR-4 Survival cap**: if the thief survives `survival_threshold` steps uncaught, the thief
  wins the sub-game.
- **FR-5 Scoring**: fixed point table (Appendix ו) — capture: cop 20 / thief 5; survival:
  cop 5 / thief 10; tie: 2/2; technical_loss: 0/0. Never hardcoded outside `domain/scoring.py`.
- **FR-6 Communication**: each peer is simultaneously an MCP server and client (FastMCP),
  P2P, no shared server (stage 2).
- **FR-7 Strategy**: the move decision is always a pure algorithm — never delegated to an
  LLM. Default ships as a Manhattan-distance + Bayesian-belief heuristic requiring zero LLM
  tokens (stage 3-4).
- **FR-8 Language/scent**: free-text hints capped at `hint_max_words`, may lie; pheromone
  scent-trail belief modeling (stage 4).
- **FR-9 Integrity**: every move sealed via SHA-256 commit-reveal with a fresh nonce; a
  mutual post-game audit re-verifies every step (stage 6).
- **FR-10 Reporting**: four standardized JSON artifacts per game
  (`declaration_/config_/log_/result_<game_id>...json`), auto-emailed via Gmail API to the
  grader address, rate-limited by a Gatekeeper (stage 7).
- **FR-11 Config split**: shared, signed terms live in `config/game.json` (byte-identical to
  the thief repo's copy); private, local-only settings live in `config/game.toml`.

## Non-functional requirements
- **NFR-1**: every Python source file ≤ 150 lines of code.
- **NFR-2**: ≥ 85% test coverage (`pytest --cov`).
- **NFR-3**: zero Ruff violations (`ruff check .`).
- **NFR-4**: no hardcoded game-rule numbers outside `config/game.json` and
  `domain/scoring.py` (which mirrors the book's fixed table verbatim, by design).
- **NFR-5**: no secrets committed (`credentials.json`, `token.json`, `.env` all gitignored).
- **NFR-6**: `uv`-managed dependencies only (no bare `pip`/`venv`).
- **NFR-7**: semantic versioning starting at `1.0.0`.
- **NFR-8**: works fully with zero LLM calls (template trash-talk provider, 0 tokens) —
  the game must be completable and gradeable with no API keys configured.

## Out of scope for this repo
- The thief's own strategy logic (lives entirely in the sibling `bb-ai-12-thief` repo).
- Any shared runtime process between the two repos — they only ever talk over the network.

## Status
All 7 book-mandated build stages complete, plus the real turn-taking protocol and automatic
end-of-game detection (2026-08-20): FR-1 through FR-9 implemented and tested and now exercised
genuinely bidirectionally — both peers' inbound and outbound moves are real strategy decisions
exchanged via the book's confirmed Commit→Acknowledge→Reveal protocol (see
`docs/PRD_turn_protocol.md`), and `PeerRuntime.run_turn_loop` now stops automatically on
capture or survival instead of always running the full requested turn count (see
`docs/PRD_end_of_game_detection.md`). FR-9's audit is still local self-audit per peer, not yet
a mutual end-of-game log exchange; FR-10 (the four JSON artifacts build and write correctly;
Gmail sending is built, unit-tested, **and verified with a real send** to
`rmisegal+uoh26finalgame@gmail.com` — see `docs/PRD_reporting_shell.md`; a `send-report`
command that fires automatically off the new outcome-detection is still open); FR-11 (loading
+ a pre-game config-agreement check, no full negotiation handshake yet).

**The hard blocker found while verifying end-of-game detection is now fixed**: two
freshly-started, independent peer processes previously failed on round 1 due to a missing
synchronization point in the wire protocol (the book's Acknowledge step never actually waited
for both sides to commit before either revealed). `TurnHandler.wait_for_own_reveal` now blocks
an inbound reveal until this peer's own reveal is locally ready, closing the race. A second,
lower-severity issue found in the same verification pass — whichever side reached `GAME OVER`
first used to exit immediately, occasionally cutting off the opponent's still-in-flight
final-round call — is also fixed: `peer` now waits briefly after the outcome leaves `ONGOING`
before exiting. Re-verified live: a full 40-turn two-process run now exchanges real
commit-reveal rounds continuously, the police side auto-detects `GAME OVER` correctly, and
both processes exit cleanly with no errors. No known blockers remain for a real live match.
See `docs/TODO.md` for full detail.

See `docs/PRD_base_logic.md` / `docs/PRD_mcp_infra.md` / `docs/PRD_strategy.md` /
`docs/PRD_language_scent.md` / `docs/PRD_cloud_tunnel.md` / `docs/PRD_security_crypto.md` /
`docs/PRD_reporting_shell.md` / `docs/PRD_turn_protocol.md` / `docs/PRD_end_of_game_detection.md`
for stage-specific detail and `docs/TODO.md` for what's next (deferred integration work, not a
new stage).
