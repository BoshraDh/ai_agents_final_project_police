"""Tests for the league kit's terms translation and negotiate signature."""

from __future__ import annotations

from bb_ai_12_police.league.terms import terms_signature, to_wire_terms, verify_signature
from bb_ai_12_police.shared.config_manager import ConfigManager

_EXPECTED_CANONICAL = (
    '{"axis_origin_corner":"top-left","axis_start_index":0,"barriers_max":14,"board_size":7,'
    '"cop_start":[0,0],"decay_per_step":0.1,"emit_intensity":0.9,"hint_max_words":15,'
    '"max_steps":35,"min_center_intensity":0.5,"num_games":6,"setting":"New York",'
    '"smell_grid_size":5,"thief_start":[3,3]}'
)


def test_to_wire_terms_matches_the_leagues_exact_canonical_string():
    from bb_ai_12_police.crypto.commit_reveal import canonical_json

    shared = ConfigManager(".").load_shared()
    assert canonical_json(to_wire_terms(shared)) == _EXPECTED_CANONICAL


def test_terms_signature_round_trips_through_verify_signature():
    terms = {"a": 1}
    nonce = "deadbeef"
    signature = terms_signature(terms, nonce)
    assert verify_signature(terms, nonce, signature)


def test_verify_signature_fails_for_a_tampered_terms_dict():
    terms = {"a": 1}
    nonce = "deadbeef"
    signature = terms_signature(terms, nonce)
    assert not verify_signature({"a": 2}, nonce, signature)
