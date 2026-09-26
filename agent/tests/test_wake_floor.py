"""How short a wake the model is allowed to ask for.

One raid, three wake plans:

    seq 2066  wake_in_hours 2
    seq 2138  wake_in_hours 3     <- mid-chase, a raider carrying a colonist to the edge
    seq 2268  wake_in_hours 0.5

At seq 2138 the model chose to sleep three in-game hours during a kidnapping. Even had it asked for the
shortest wake the harness allowed, 0.5 hours was longer than the whole chase. The floor was the ceiling on
how urgently it could think.

This is a floor and not a schedule: it only widens what the model can ask for.
"""
from __future__ import annotations

from rimagent.runner import wake_floor

PLAY = {"min_wake_hours": 8, "min_wake_hours_urgent": 0.1}


def test_a_calm_step_keeps_the_long_floor():
    assert wake_floor(PLAY, urgent=False) == 8


def test_an_urgent_step_may_ask_for_in_game_minutes():
    assert wake_floor(PLAY, urgent=True) == 0.1


def test_a_model_driven_speed_counts_as_urgent():
    assert wake_floor(PLAY, urgent=False, model_speed=0) == 0.1


def test_the_defaults_are_the_old_fixed_floors():
    assert wake_floor({}, urgent=True) == 0.5
    assert wake_floor({}, urgent=False) == 3


# ---------------------------------------------------- the fight outlives the step that woke on it
# Urgency is a property of the step's trigger; a raid is a property of the world. A step that woke on a mood
# alert while a raider was carrying a colonist to the edge was calm, so a wake plan of half an hour was raised
# to the calm floor of eight in-game hours.

def test_hostiles_on_the_map_lower_the_floor_on_a_calm_step():
    assert wake_floor(PLAY, urgent=False, hostiles=True) == 0.1


def test_no_hostiles_and_a_calm_step_keeps_the_long_floor():
    assert wake_floor(PLAY, urgent=False, hostiles=False) == 8


def test_hostiles_present_reads_the_summary_and_survives_a_refusal():
    from types import SimpleNamespace

    from rimagent.bridge import BridgeError
    from rimagent.runner import Runner

    def bridge(summary):
        return SimpleNamespace(call=lambda method, **p: summary if method == "state.summary" else {})

    assert Runner.hostiles_present(SimpleNamespace(bridge=bridge({"hostiles": [{"id": "h1"}]}))) is True
    assert Runner.hostiles_present(SimpleNamespace(bridge=bridge({}))) is False

    def refuse(method, **p):
        raise BridgeError("no bridge")
    assert Runner.hostiles_present(SimpleNamespace(bridge=SimpleNamespace(call=refuse))) is False
