"""One line per tool call, both directions, so two peers can diff their logs.

Agreed with SMNGRP05 on 2026-08-26 after their inbound counts and our outbound
replies could not both be true: sub-game 2, they recorded 2 inbound calls while
we made 4 and got `{'ok': True}` back from their `receive_turn` for two of them.
A reply of that shape can only come from their tool actually running, so one of
the two logs is measuring something the other is not.

Every outbound call emits a PAIR of lines: `OUT` before it is sent, and then
either `OUT-OK` (carrying the reply we parsed) or `OUT-ERR` (carrying the
exception) once it resolves. The single `OUT` line alone was not enough -- it is
printed before the call, so a call that never completed looked identical on our
side to one that succeeded, which is precisely the ambiguity the log exists to
remove.

The rule for reading a diff of the two lists:
  - our OUT-OK, absent from their IN  -> the call completed for us but never ran
    on their side: lost on the wire, or answered by another process behind their
    tunnel
  - our OUT with no OUT-OK            -> the call never completed for us; ours
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


def trace(
    direction: str, tool: str, body: dict[str, Any] | None, detail: str | None = None
) -> None:
    """Trace one tool call.

    `direction` is "IN" (they called us), "OUT" (we are about to call them),
    "OUT-OK" (that call returned) or "OUT-ERR" (it failed). `detail` is an
    already-formatted `key=value` fragment appended verbatim.
    """
    stamp = dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds")
    parts = [f"[wire] {stamp} {direction:7} {tool}"]
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
    if detail is not None:
        parts.append(detail)
    print(" ".join(parts), flush=True)


def note(text: str) -> None:
    """A wire-level event that is not a tool call -- e.g. a silent reconnect."""
    stamp = dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds")
    print(f"[wire] {stamp} --  {text}", flush=True)
    sys.stdout.flush()
