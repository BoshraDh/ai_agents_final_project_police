"""Adapter for the `copthief-league-protocol` kit's 4-tool wire shape
(negotiate/receive_turn/submit_audit/receive_control) — an alternate,
opt-in transport used only against opponents that run the kit's client,
alongside (not replacing) this repo's own submit_commit/submit_reveal
protocol for every other pairing. See `docs/PRD_league_adapter.md`.
"""
