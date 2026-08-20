"""`declare` — print this peer's sealed Step-0 declaration."""

from __future__ import annotations

import json

from bb_ai_12_police.crypto.step0 import Step0Declaration
from bb_ai_12_police.shared.config_manager import ConfigManager


def run(repo_root: str) -> int:
    team_code = ConfigManager(repo_root).load_private()["game"]["group_id"]
    declaration = Step0Declaration.create(team_code)
    print(
        json.dumps(
            {
                "payload": declaration.payload,
                "nonce": declaration.nonce,
                "commitment": declaration.commitment,
            },
            indent=2,
        )
    )
    print(f"verify() = {declaration.verify()}")
    return 0
