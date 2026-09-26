"""Which wakes run at danger_think_speed, and what happens when the decisive event arrives mid-step.

Finding 26. Two functions decided what an event does and they read different data: `is_critical` classified
the event, `is_urgent` substring-matched the sentence rendered from it. So `combat_engaged`, whose kind is
"orders" and whose trigger reads "event: orders: combat_engaged 1 hostiles, 1 drafted", could break into a
running step and did not make that step urgent. Observed a minute apart in episode 1 day 3: the warning that
a fight may start paused the clock, the report that the fight *is* happening did not.

The second half cost two colonists. A step that begins calm cannot be raised by what arrives inside it.
"""
from __future__ import annotations

from typing import Any

from rimagent.context import Context
from rimagent.registry import Registry
from rimagent.runner import Runner

KINDS = {"dialog", "danger", "manhunter", "hostile_group", "colonist_downed", "colonist_died", "mental_break", "building_lost"}
EVENTS = {"combat_engaged"}

COMBAT = {"kind": "orders", "text": "combat_engaged 1 hostiles, 1 drafted", "data": {"event": "combat_engaged"}}
RESCUE = {"kind": "orders", "text": "rescue Fugl", "data": {"event": "rescue"}}
DOWNED = {"kind": "colonist_downed", "text": "Kangjoon is down"}


class FakeBridge:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def call(self, method, **params):
        self.calls.append((method, params))
        return {}


class FakeBus:
    def emit(self, kind, data=None):
        pass


class FakeRunner:
    """Just the attributes the urgency methods touch, so the real ones can be called against it."""

    def __init__(self, play: dict[str, Any] | None = None):
        self.cfg = {"play": play or {"danger_think_speed": 0}}
        self.bridge = FakeBridge()
        self.bus = FakeBus()
        self.critical_kinds = set(KINDS)
        self.critical_events = set(EVENTS)
        self.wake_event: dict[str, Any] | None = None
        self.cooled_event: dict[str, Any] | None = None
        self.urgent_step = False
        self.ctx = Context(bridge=self.bridge, llm=None, registry=Registry(), config=self.cfg, emit=lambda k, d: None)  # type: ignore[arg-type]


def _urgent(trigger: str, event: dict[str, Any] | None = None, play: dict[str, Any] | None = None) -> bool:
    r = FakeRunner(play)
    r.wake_event = event
    return Runner.is_urgent(r, trigger)


# ---------------------------------------------------- classify the event, not the sentence

def test_combat_engaged_is_urgent_although_no_critical_kind_is_in_its_trigger():
    trigger = "event: orders: combat_engaged 1 hostiles, 1 drafted"
    assert not any(k in trigger for k in KINDS), "the trigger text must not contain a critical kind, or this proves nothing"
    assert _urgent(trigger, COMBAT)


def test_an_ordinary_standing_order_is_not_urgent():
    assert not _urgent("event: orders: rescue Fugl", RESCUE)


def test_a_critical_kind_is_urgent_by_its_kind():
    assert _urgent("event: colonist_downed: Kangjoon is down", DOWNED)


def test_a_letter_whose_title_contains_a_critical_kind_is_no_longer_promoted_by_accident():
    """Substring matching was positional, not structural: any High alert with "danger" in its label became urgent."""
    assert not _urgent("alert (High): Danger of infection")


def test_a_high_game_alert_is_not_urgent_and_a_critical_one_is():
    assert not _urgent("alert (High): Medical treatment needed")
    assert _urgent("alert (Critical): Colonist starving")


def test_a_waking_watcher_alert_and_an_operator_wake_stay_urgent():
    assert _urgent("watcher alert: FIRE: Critical alert: Fire!")
    assert _urgent("operator message")


def test_a_scheduled_check_in_is_not_urgent():
    assert not _urgent("scheduled check-in")


# ---------------------------------------------------- promotion, for what arrives after the step began

def test_promotion_pauses_the_game_and_marks_the_step_urgent():
    r = FakeRunner({"danger_think_speed": 0})
    Runner.promote_to_urgent(r)
    assert r.urgent_step is True
    assert r.ctx.extra["urgent"] is True
    assert r.ctx.extra["think_speed"] == 0
    assert ("game.pause", {"paused": True}) in r.bridge.calls


def test_promotion_honours_a_configured_danger_speed_rather_than_always_pausing():
    r = FakeRunner({"danger_think_speed": 1})
    Runner.promote_to_urgent(r)
    assert r.ctx.extra["think_speed"] == 1
    assert ("game.speed", {"speed": 1}) in r.bridge.calls
    assert ("game.pause", {"paused": False}) in r.bridge.calls


def test_promotion_clears_a_model_chosen_speed_so_the_runner_restores_play_speed():
    r = FakeRunner()
    r.ctx.extra["model_speed"] = 3
    Runner.promote_to_urgent(r)
    assert r.ctx.extra["model_speed"] is None


def test_a_promoted_step_takes_the_urgent_wake_floor():
    """The wake floor is read off urgent_step, not off the local computed at step start, so promotion reaches it."""
    r = FakeRunner()
    r.urgent_step = Runner.is_urgent(r, "alert (High): Medical treatment needed")
    assert r.urgent_step is False
    Runner.promote_to_urgent(r)
    assert r.urgent_step is True


# ---------------------------------------------------- the wiring: the wake carries its event to is_urgent

class WakeRunner(FakeRunner):
    """Enough of a Runner to call the real wake_trigger and check_interrupts."""

    def __init__(self, events: list[dict[str, Any]] | None = None, play: dict[str, Any] | None = None):
        super().__init__(play)
        self.cfg["play"].setdefault("event_cooldown_hours", 1)
        self.force_think = None
        self.pending_alerts: list[dict[str, Any]] = []
        self.wake_kinds: set[str] = set()
        self._last_step_end_tick = 0
        self.next_wake_tick = 10 ** 9
        self._polled = events or []

    def game_alert_trigger(self, tick):  # noqa: ARG002
        return None

    def poll_events(self):
        return self._polled

    def promote_to_urgent(self):
        Runner.promote_to_urgent(self)


def _wake(events: list[dict[str, Any]]) -> tuple[str | None, bool]:
    r = WakeRunner()
    trigger = Runner.wake_trigger(r, 5000, events)
    return trigger, Runner.is_urgent(r, trigger or "")


def test_the_combat_wake_arrives_at_is_urgent_with_its_event_attached():
    trigger, urgent = _wake([COMBAT])
    assert trigger == "event: orders: combat_engaged 1 hostiles, 1 drafted"
    assert urgent is True


def test_a_scheduled_wake_carries_no_event():
    r = WakeRunner()
    r.next_wake_tick = 0
    assert Runner.wake_trigger(r, 5000, []) == "scheduled check-in"
    assert r.wake_event is None


def test_the_event_does_not_survive_into_the_next_wake():
    r = WakeRunner()
    Runner.wake_trigger(r, 5000, [COMBAT])
    assert r.wake_event is COMBAT
    r.next_wake_tick = 0
    Runner.wake_trigger(r, 5000, [])
    assert r.wake_event is None


def test_an_urgent_event_arriving_mid_step_promotes_the_step():
    r = WakeRunner(events=[DOWNED])
    r.urgent_step = False
    assert Runner.check_interrupts(r) == ["colonist_downed: Kangjoon is down"]
    assert r.urgent_step is True
    assert ("game.pause", {"paused": True}) in r.bridge.calls


def test_an_ordinary_event_arriving_mid_step_leaves_the_step_alone():
    r = WakeRunner(events=[RESCUE])
    assert Runner.check_interrupts(r) == []
    assert r.urgent_step is False
    assert r.bridge.calls == []
