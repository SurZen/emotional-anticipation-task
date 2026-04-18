"""
Select a deck at runtime and return the matching FINAL conditions file.

Builder "Begin Experiment" snippet:

from experiment.code.deck_router import resolve_conditions_file
deck_id = expInfo.get('deck_id', 'EAT_1')
conditions_file = resolve_conditions_file(deck_id)

Then set your TrialHandler loop conditions to: $conditions_file
"""

from __future__ import annotations
import os

VALID_DECKS = {f"EAT_{i}" for i in range(1, 6)}

def resolve_conditions_file(deck_id: str) -> str:
    deck_id = (deck_id or "").strip()
    if deck_id not in VALID_DECKS:
        raise ValueError(f"Invalid deck_id '{deck_id}'. Must be one of: {sorted(VALID_DECKS)}")
    return os.path.join("conditions", deck_id, f"trials_{deck_id}.csv")
