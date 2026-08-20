"""Collects this peer's hardware/software environment for Step-0 (crypto/step0.py)."""

from __future__ import annotations

import platform
import sys
from typing import Any


def collect_sysinfo() -> dict[str, Any]:
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "machine": platform.machine(),
    }
