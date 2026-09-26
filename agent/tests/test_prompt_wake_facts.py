"""The system prompt states the urgent wake floor and the danger-step speed from config, not a fixed range."""
from __future__ import annotations

from rimagent.loop import _fmt, load_prompt, wake_text

SYSTEM = load_prompt("system", "")


def _render(play: dict) -> str:
    return _fmt(SYSTEM, **wake_text(play))


def test_the_prompt_states_the_configured_floor():
    text = _render({"min_wake_hours_urgent": 0.1, "danger_think_speed": 0})
    assert "the shortest `wake_in_hours` is 0.1 in-game hours (6 in-game minutes)" in text


def test_the_default_floor_is_the_runners():
    assert "is 0.5 in-game hours (30 in-game minutes)" in _render({})


def test_a_paused_danger_step_says_paused():
    assert "is paused while you think on danger steps" in _render({"danger_think_speed": 0})


def test_a_running_danger_step_says_its_speed():
    assert "runs at speed 1 while you think on danger steps" in _render({"danger_think_speed": 1})


def test_the_fixed_range_is_gone():
    text = _render({})
    assert "0.5-2 hours" not in text
    assert "{urgent_wake" not in text and "{danger_think}" not in text
