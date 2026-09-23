"""The four stale-fight events wake the agent at once and interrupt a step (rimworld-llm#111 item 2)."""
from __future__ import annotations

from pathlib import Path

import yaml

from rimagent.tools import meta

KINDS = ("target_out_of_range", "target_lost_los", "approach_ended_no_shot", "carrier_near_edge")
CONFIG = Path(__file__).resolve().parents[2] / "config.yaml"


def _play() -> dict:
    return yaml.safe_load(CONFIG.read_text())["play"]


def test_the_events_are_wake_kinds():
    assert set(KINDS) <= set(_play()["wake_on_kinds"])


def test_the_events_are_critical():
    assert set(KINDS) <= set(_play()["critical_kinds"])


def test_end_turn_names_the_events():
    for kind in KINDS:
        assert kind in meta.end_turn._tool_desc
