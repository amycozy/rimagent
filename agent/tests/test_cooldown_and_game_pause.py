"""A wake event inside the cooldown, and a game that pauses itself between steps.

In one episode a step ended at tick ~77055. At tick 80396 the letter "Monitor lizard hunting Thunkalatha"
came, 1.3 h later, inside the 3 h cooldown. The event was dropped. RimWorld auto-paused on the letter, so the
tick stopped and the scheduled wake at 97053 could not come. The run sat paused with no step for about 40 real
minutes, until the operator pressed Think now.
"""
from __future__ import annotations

from types import SimpleNamespace

from rimagent.runner import Runner

LETTER = {"kind": "letter", "text": "Monitor lizard hunting Thunkalatha"}


def _runner() -> SimpleNamespace:
    return SimpleNamespace(force_think=None, pending_alerts=[], cfg={"play": {"event_cooldown_hours": 3}},
                           wake_kinds={"letter"}, ctx=SimpleNamespace(wake=SimpleNamespace(on_kinds=[])),
                           critical_kinds=set(), critical_events=set(), wake_event=None, cooled_event=None, _game_paused_since=None,
                           _last_step_end_tick=77055, next_wake_tick=97053,
                           game_alert_trigger=lambda tick: None)  # noqa: ARG005


def test_an_event_inside_the_cooldown_does_not_wake_at_once():
    r = _runner()
    assert Runner.wake_trigger(r, 80396, [LETTER]) is None
    assert r.cooled_event is LETTER


def test_the_held_event_wakes_when_the_cooldown_ends():
    r = _runner()
    Runner.wake_trigger(r, 80396, [LETTER])
    assert Runner.wake_trigger(r, 81000, []) is None
    trigger = Runner.wake_trigger(r, 77055 + 3 * 2500, [])
    assert trigger == "event held through the cooldown: letter: Monitor lizard hunting Thunkalatha"


def test_a_game_paused_inside_the_cooldown_wakes_with_the_held_event():
    r = _runner()
    Runner.wake_trigger(r, 80396, [LETTER])
    trigger = Runner.wake_trigger(r, 80396, [], game_paused=True)
    assert trigger.startswith("game paused between steps; event held through the cooldown: letter")


def test_a_game_paused_with_nothing_held_still_wakes():
    assert Runner.wake_trigger(_runner(), 80396, [], game_paused=True) == "game paused between steps"


def test_only_the_first_held_event_is_kept():
    r = _runner()
    Runner.wake_trigger(r, 80396, [LETTER, {"kind": "letter", "text": "later"}])
    assert r.cooled_event is LETTER


def test_a_short_pause_is_not_a_pause_between_steps(monkeypatch):
    r = _runner()
    now = [1000.0]
    monkeypatch.setattr("rimagent.runner.time.time", lambda: now[0])
    assert Runner.game_paused_between_steps(r, {"paused": True}) is False
    now[0] += 2
    assert Runner.game_paused_between_steps(r, {"paused": True}) is False
    now[0] += 2
    assert Runner.game_paused_between_steps(r, {"paused": True}) is True
    assert Runner.game_paused_between_steps(r, {"paused": False}) is False
    assert r._game_paused_since is None
