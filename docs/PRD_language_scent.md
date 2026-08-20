# PRD — Stage 4: Language + Scent

## Goal
Add the two "language" ingredients the book stages here: a digital pheromone/scent-trail
field, and zero-token trash-talk hint generation wired into the wire protocol. The move
decision is still — and will always be — chosen by pure Python, never the LLM (book ch.6.5).

## Delivered
| Module | Responsibility | Book reference |
|---|---|---|
| `domain/pheromones.py` | `PheromoneField` — τij(t+1)=max(0,(1-ρ)τij(t)+Δτij); `step(pos)` deposits+decays, `intensity_at`, `strongest_cell` | pheromone mechanic (Appendix ו: center_intensity=0.9, decay=0.10, grid_size=5) |
| `llm/provider_base.py` | `TrashTalkProvider` — abstract `_generate(turn)`; concrete `hint(turn)` centralizes the `hint_max_words` truncation | ch.6.5 (LLM restricted to text) |
| `llm/template_provider.py` | `TemplateProvider` — 0-token canned sentence bank, the required zero-LLM default (NFR-8) | — |
| `llm/resolve_provider.py` | `resolve_provider(private, shared)` — factory reading `[trash_talk].provider`; `ollama`/`claude_api`/`claude_cli` raise `NotImplementedError` until a later stage | Appendix ב |
| `mcp/server.py` / `mcp/client.py` | `receive_move`/`McpTransport.send_move` gain a `hint: str = ""` field on both the request and the (still-stub) reply | ch.5 |
| `runtime/peer_runtime.py` | `run_turn_loop` generates a real hint each turn via `trash_talk.hint(turn)`, sends it alongside the move, and steps `opponent_scent` (a `PheromoneField`) with the tracked opponent position | ch.7 |

## Design decisions
- **Pheromone spatial footprint not yet implemented.** The one formula this session has
  confirmed with confidence is the single-cell decay+deposit recurrence. `pheromone_grid_size`
  (5) is read and stored on `PheromoneField` but not yet used to spread a deposit across a
  neighborhood — the book's exact spatial falloff shape (uniform vs. weighted) needs
  re-confirming against the book text before that's built, rather than guessed at here. Open
  item in `docs/TODO.md`.
- **`opponent_scent` is currently redundant with `BeliefState`.** Since moves are still
  honestly relayed (no deception, no crypto yet), `BeliefState.opponent_position` is already
  exact — so depositing scent at that exact position doesn't yet add new information. It's
  wired in now so the module is real and tested, and becomes load-bearing once stage 4's own
  deception allowance (FR-8: the thief's hints may lie) and stage 6's crypto make position
  genuinely uncertain and the scent trail the actual signal being reasoned about.
- **Hints are flavor text, not yet position claims.** `TemplateProvider` cycles a fixed
  sentence bank; it doesn't yet reference a real or false position. Tying hint content to
  (possibly deceptive) position claims is deferred until there's an audit layer that makes a
  caught lie costly — building deception without that would just be an unpunished no-op.
- **Same stage-2/3 wire-protocol boundary holds.** `mcp/server.py`'s inbound stub still always
  replies STAY with a fixed placeholder hint (`"..."`). Real inbound hints wait on the same
  synchronized turn-taking protocol already deferred in `docs/PRD_strategy.md`.

## Acceptance criteria (all met)
- [x] `PheromoneField.step` matches τij(t+1)=max(0,(1-ρ)τij(t)+Δτij) exactly for the
      single-cell case; decayed-to-zero cells are pruned from the sparse dict.
- [x] `TemplateProvider.hint(turn)` never exceeds `hint_max_words` words, for any turn.
- [x] `resolve_provider` defaults to `template`, and raises `NotImplementedError` with a clear
      message for any other configured provider name.
- [x] **Manually verified with real hints on both sides**: ran `bb-ai-12-thief peer --turns 4`
      and `bb-ai-12-police peer --turns 4` concurrently. All four of the thief's outbound
      turns carried real, distinct template lines (not empty/placeholder text), and the
      police's inbound stub correctly logged both the direction and the hint it received. The
      same benign stage-2/3 teardown race recurred once the shorter-running side's script
      exited first — expected, not a new defect.
- [x] `uv run pytest -q --cov=src` passes at 95% coverage (57 tests); `uv run ruff check .` is
      clean.

## Explicitly deferred to later stages
- Spatial pheromone spread across `pheromone_grid_size`.
- Deceptive/position-linked hints (needs the crypto audit to make lying costly) — stage 6.
- Real LLM trash-talk providers (`ollama`/`claude_api`/`claude_cli`).
- Inbound `receive_move` replying with a real move/hint (synchronized turn-taking protocol).
- Barrier placement — still not decided by any brain; wire protocol still doesn't carry it.
- Cloud tunneling — stage 5.
- Commit-reveal sealing, nonces, Step-0 declaration, real negotiation handshake — stage 6.
- Gmail reporting, GUI, replay viewer — stage 7.
