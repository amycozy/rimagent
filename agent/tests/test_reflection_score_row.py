"""The episode reflection sees this episode's score row before it is recorded."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from rimagent import reflect, scorecard

pytestmark = pytest.mark.usefixtures("clean_brain")

ROW = {"episode": 2, "seed": "rimagent-2", "days": 13, "colonists": 0, "deaths": 3, "wealth": 9000.0,
       "score": 532.0, "assisted": False, "ended": "no colonists left"}


def test_pending_row_is_the_last_row():
    scorecard.record({"episode": 1, "seed": "rimagent-1", "score": 414.0, "brain_sha": "254de2c0"})
    lines = scorecard.history_text(12, pending=ROW).splitlines()
    assert len(lines) == 3
    assert lines[-1].startswith("2 | rimagent-2 | 13 |")
    assert "| 532.0 |" in lines[-1]


def test_pending_row_counts_against_last():
    for i in range(3):
        scorecard.record({"episode": i, "score": float(i)})
    lines = scorecard.history_text(2, pending=ROW).splitlines()
    assert [l.split(" | ")[0] for l in lines[1:]] == ["2", "2"]


def test_reflection_prompt_holds_the_score(monkeypatch):
    seen = {}

    def fake_think(ctx, prompt, **kw):
        seen["prompt"] = prompt
        return SimpleNamespace(notes="done")

    monkeypatch.setattr(reflect, "think", fake_think)
    reflect.episode(SimpleNamespace(), [], [], "no colonists left", 13, row=ROW)
    assert "532.0" in seen["prompt"]
