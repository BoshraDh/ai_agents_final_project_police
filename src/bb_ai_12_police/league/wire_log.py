"""One line per tool call, both directions, so two peers can diff their logs.

Agreed with SMNGRP05 on 2026-08-26 after their inbound counts and our outbound
replies could not both be true: sub-game 2, they recorded 2 inbound calls while
we made 4 and got `{'ok': True}` back from their `receive_turn` for two of them.
A reply of that shape can only come from their tool actually running, so one of
the two logs is measuring something the other is not.

The rule for reading a diff of the two lists:
  - in our OUT, absent from their IN  -> lost on the wire (or landed on another
    process behind their tunnel)
  - in both, but they never acted     -> their side
  - never in our OUT                  -> our side

Every line is flushed immediately: stdout is block-buffered when redirected to
a file, which is why our own turn counts appeared to lag reality during the
live sub-games.
"""

from __future__ import annotations

import datetime as dt
import sys
from typing import Any

_COMMIT_PREFIX_LEN = 12


def trace(direction: str, tool: str, body: dict[str, Any] | None) -> None:
    """`direction` is "OUT" (we called them) or "IN" (they called us)."""
    stamp = dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds")
    parts = [f"[wire] {stamp} {direction:3} {tool}"]
    body = body or {}
    step = body.get("step")
    if step is not None:
        parts.append(f"step={step}")
    sub_game = body.get("sub_game_number")
    if sub_game is not None:
        parts.append(f"sub_game={sub_game}")
    commit = body.get("commit")
    if isinstance(commit, str):
        parts.append(f"commit={commit[:_COMMIT_PREFIX_LEN]}")
    print(" ".join(parts), flush=True)


def note(text: str) -> None:
    """A wire-level event that is not a tool call -- e.g. a silent reconnect."""
    stamp = dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds")
    print(f"[wire] {stamp} --  {text}", flush=True)
    sys.stdout.flush()
