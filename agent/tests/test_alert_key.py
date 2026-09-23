"""The game alert cooldown holds for an alert whose label counts down."""
from __future__ import annotations

from types import SimpleNamespace

from rimagent.runner import TICKS_PER_HOUR, Runner, alert_key


def test_key_is_the_id_when_sent():
    assert alert_key({"id": "Alert_QuestExpiring", "label": "Quest expires in 7 hours"}) == "Alert_QuestExpiring"


def test_key_without_id_drops_digits():
    assert alert_key({"label": "Quest expires in 24 hours"}) == alert_key({"label": "Quest expires in 11 hours"})
    assert alert_key({"label": "Need batteries"}) == "Need batteries"


def trigger(runner, labels, tick):
    runner._alerts_at = 0.0
    runner.bridge = SimpleNamespace(call=lambda method: [{"label": x, "priority": "High"} for x in labels])
    return Runner.game_alert_trigger(runner, tick)


def test_countdown_label_wakes_once_per_cooldown():
    runner = SimpleNamespace(cfg={"play": {"alert_wake_priorities": ["High"], "alert_rewake_hours": 24}}, _seen_alerts={})
    assert trigger(runner, ["Quest expires in 24 hours"], 0) == "alert (High): Quest expires in 24 hours"
    assert trigger(runner, ["Quest expires in 11 hours"], 13 * TICKS_PER_HOUR) is None
    assert trigger(runner, ["Quest expires in 7 hours"], 17 * TICKS_PER_HOUR) is None
