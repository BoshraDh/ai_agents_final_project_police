# PRD — Stage 1: Base Logic

## Goal
Grid, movement, barriers, capture, scoring — as a pure, dependency-free domain layer, with
no networking, no crypto, no LLM. Runnable and testable in a single process.

## Delivered
| Module | Responsibility | Book reference |
|---|---|---|
| `domain/protocol.py` | `Position`, `Direction`, `Role`, `GameOutcome`, `MoveAction` | ch.3 |
| `domain/board.py` | grid bounds, legal directions, start positions | ch.3.2-3.3 |
| `domain/barriers.py` | police-only barrier placement, capped, adjacency rule | ch.3.4 |
| `domain/rules.py` | move legality, capture/survival resolution | ch.3.4-3.5 |
| `domain/scoring.py` | fixed score table | Appendix ו |
| `shared/config_manager.py` | loads `game.json` + `game.toml`, exposes SHA-256 of the shared file | Appendix ב |
| `cli.py` | `check-config` subcommand (smoke-test the config load) | — |

## Acceptance criteria (all met)
- [x] `Board(size<7)` raises `ValueError` (book's stated minimum).
- [x] Moves off the grid or onto a barrier are rejected by `is_legal_move`.
- [x] Barriers can only be placed adjacent to (or on) the police's own current cell, capped
      at `max_barriers`, and placement is irreversible (no removal API exists).
- [x] `resolve_capture_claim` is a pure geometric equality check — the crypto layer (stage 6)
      is what actually makes a false claim costly, not this module.
- [x] `check_survival` / `outcome_after_step` match the book's two win conditions exactly.
- [x] `score_for`/`scores_for_both` return exactly Appendix ו's numbers: 20/5 (capture),
      5/10 (survival), 2/2 (tie), 0/0 (technical loss).
- [x] `ConfigManager` round-trips `config/game.json` + `config/game.toml` and can compute a
      stable SHA-256 of the shared file's raw bytes.
- [x] `uv run pytest -q --cov=src` passes at 97% coverage; `uv run ruff check .` is clean.

## Explicitly deferred to later stages
- Networking (MCP server/client) — stage 2.
- Any strategy beyond "legal moves exist" — stage 3.
- Pheromones/belief/hints — stage 4.
- Commit-reveal sealing, nonces, Step-0 declaration, pre-game SHA-256 handshake — stage 6.
  (`ConfigManager.game_json_sha256()` exists now because the domain layer needed *a* stable
  hash function for tests; the actual handshake/audit logic that consumes it is stage 6.)
- Gmail reporting, GUI, replay viewer — stage 7.
