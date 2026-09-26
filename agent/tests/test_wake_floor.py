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


def test_summary_survives_a_refusal():
    from types import SimpleNamespace

    from rimagent.bridge import BridgeError
    from rimagent.runner import Runner

    def refuse(method, **p):
        raise BridgeError("no bridge")
    assert Runner.summary(SimpleNamespace(bridge=SimpleNamespace(call=refuse))) == {}


# ---------------------------------------------------- a casualty lowers the floor
# In one episode a colonist lay downed with 2.2 h to bleed out. No hostile was left, so the step was calm, and
# a wake of 0.5 h was raised to 8 h. He died 3.2 h later with no step between.

def _world_floor(summary, urgent=False):
    from types import SimpleNamespace

    from rimagent.runner import Runner

    play = {"min_wake_hours": 8, "min_wake_hours_urgent": 0.5, "bleed_out_urgent_hours": 6}
    r = SimpleNamespace(cfg={"play": play}, ctx=SimpleNamespace(extra={}),
                        bridge=SimpleNamespace(call=lambda method, **p: summary if method == "state.summary" else {}))
    r.summary = lambda: Runner.summary(r)
    return Runner.world_floor(r, urgent)


def test_hostiles_on_the_map_take_the_urgent_floor():
    assert _world_floor({"hostiles": [{"id": "h1"}]}) == 0.5


def test_a_calm_summary_keeps_the_calm_floor():
    assert _world_floor({"hostiles": [], "downed": 0}) == 8


def test_a_downed_colonist_takes_the_urgent_floor():
    assert _world_floor({"hostiles": [], "downed": 1}) == 0.5


def test_a_colonist_bleeding_out_soon_takes_the_urgent_floor():
    assert _world_floor({"downed": 0, "bleed_out_hours": 2.2}) == 0.5


def test_a_slow_bleed_keeps_the_calm_floor():
    assert _world_floor({"downed": 0, "bleed_out_hours": 20}) == 8
