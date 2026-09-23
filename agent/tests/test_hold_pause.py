"""A step that runs paused stays paused: the model's speed change waits for end_turn."""
from types import SimpleNamespace

from rimagent.registry import Registry
from rimagent.runner import Runner


class Bridge:
    def __init__(self):
        self.calls = []

    def call(self, method, **params):
        self.calls.append((method, params))
        return {"ok": True}


def stub(think_speed_urgent=0, think_speed_calm=1):
    return SimpleNamespace(
        cfg={"play": {"danger_think_speed": think_speed_urgent, "think_speed": think_speed_calm, "speed": 3}},
        bridge=Bridge(),
        ctx=SimpleNamespace(extra={}),
        bus=SimpleNamespace(emit=lambda *a, **k: None),
        thinking=False,
    )


def registry():
    reg = Registry()
    reg.add_bridge_methods([{"method": "game.speed", "doc": ""}, {"method": "game.pause", "doc": ""}])
    return reg


def test_urgent_step_holds_the_pause_and_applies_the_speed_at_the_end():
    r, reg = stub(), registry()

    def step():
        assert r.ctx.extra["hold_pause"] is True
        reg.execute(SimpleNamespace(bridge=r.bridge, extra=r.ctx.extra), "rw_game_speed", {"speed": 1})
        assert ("game.speed", {"speed": 1}) not in r.bridge.calls

    Runner.with_pause(r, step, urgent=True)
    assert r.ctx.extra["hold_pause"] is False
    assert r.bridge.calls[0] == ("game.pause", {"paused": True})
    assert r.bridge.calls[-2:] == [("game.speed", {"speed": 1}), ("game.pause", {"paused": False})]


def test_calm_step_does_not_hold():
    r, reg = stub(), registry()

    def step():
        assert r.ctx.extra["hold_pause"] is False
        reg.execute(SimpleNamespace(bridge=r.bridge, extra=r.ctx.extra), "rw_game_speed", {"speed": 2})
        assert ("game.speed", {"speed": 2}) in r.bridge.calls

    Runner.with_pause(r, step, urgent=False)


def test_urgent_step_with_no_pause_setting_does_not_hold():
    r = stub(think_speed_urgent=1)
    Runner.with_pause(r, lambda: None, urgent=True)
    assert r.ctx.extra["hold_pause"] is False
