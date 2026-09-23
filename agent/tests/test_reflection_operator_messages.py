"""The episode reflection shows only the operator messages sent in this episode."""
from __future__ import annotations

import datetime as dt

import pytest

from rimagent import memory, paths, reflect, scorecard

pytestmark = pytest.mark.usefixtures("clean_brain")


@pytest.fixture
def operator_file():
    paths.OPERATOR.write_text("# Tips and messages from the human operator\n"
                              "\n- [2026-09-22 19:13] Cave and Lynx were not shooting from inside.\n"
                              "\n- [2026-09-22 20:42] Old message\nwith a second line.\n"
                              "\n- [2026-09-23 02:10] Sammy needs a bed.\n", encoding="utf-8")
    yield
    paths.OPERATOR.unlink()


def _t(stamp: str) -> float:
    return dt.datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S").timestamp()


def test_messages_since_a_time(operator_file):
    assert len(memory.operator_messages()) == 3
    msgs = memory.operator_messages(_t("2026-09-22 20:42:30"))
    assert msgs == ["- [2026-09-22 20:42] Old message\nwith a second line.", "- [2026-09-23 02:10] Sammy needs a bed."]
    assert memory.operator_messages(_t("2026-09-23 03:00:00")) == []


def test_reflection_counts_this_episode_only(operator_file):
    scorecard.record({"episode": 1, "score": 414.0, "t": _t("2026-09-22 21:00:00")})
    text = reflect.operator_this_episode()
    assert text.splitlines()[0] == "1 message since the previous episode ended (2026-09-22 21:00)."
    assert "Sammy needs a bed" in text
    assert "Cave and Lynx" not in text


def test_reflection_with_no_scored_episode(operator_file):
    assert reflect.operator_this_episode().splitlines()[0] == "3 messages. No earlier episode is scored."


def test_reflection_with_no_messages():
    scorecard.record({"episode": 1, "score": 1.0})
    assert reflect.operator_this_episode().startswith("0 messages since the previous episode ended")
