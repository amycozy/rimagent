"""The kidnap and infection events wake the agent, and end_turn tells the model it can wait on them.

A wake kind the model is never told about is a wake kind it cannot use.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from rimagent.tools import meta

NEW_KINDS = ("colonist_carried", "colonist_carried_gone", "infection")
CONFIG = Path(__file__).resolve().parents[2] / "config.yaml"   # the shipped file; the suite points ROOT elsewhere


def _play() -> dict:
    return yaml.safe_load(CONFIG.read_text())["play"]


def test_the_new_events_are_default_wake_kinds():
    assert set(NEW_KINDS) <= set(_play()["wake_on_kinds"])


def test_a_colonist_being_carried_off_interrupts_a_step():
    assert "colonist_carried" in _play()["critical_kinds"]


def test_end_turn_names_the_new_kinds():
    doc = meta.end_turn._tool_desc
    for kind in NEW_KINDS:
        assert kind in doc
