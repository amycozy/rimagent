"""The age of each order summary in the Steward block."""
from __future__ import annotations

from rimagent import loop


def _lines(*orders):
    return loop.steward_orders_lines({"orders": list(orders), "rally": [40, 40, 6, 6]}, 3, 2.0)


def test_acting_line_carries_the_last_run_age():
    fire = {"id": "fire", "enabled": True, "last_run_hours_ago": 0.05, "summary": "37 fire cell(s) in the home area, 1 colonist(s) fighting", "acting_on": 37}
    assert "- fire: 37 fire cell(s) in the home area, 1 colonist(s) fighting (acting on 37) (last run 3m ago)" in _lines(fire)


def test_state_line_carries_the_last_run_age():
    combat = {"id": "combat", "enabled": True, "last_run_hours_ago": 2.5, "summary": "engaged: 1 hostile(s)", "acting_on": 0, "state": "engaged: 1 hostile(s)"}
    assert "- combat: engaged: 1 hostile(s) (last run 2.5h ago)" in _lines(combat)


def test_older_mod_without_the_age_prints_no_age():
    rescue = {"id": "rescue", "enabled": True, "summary": "rescuing Bob", "acting_on": 1}
    assert "- rescue: rescuing Bob (acting on 1)" in _lines(rescue)


def test_last_acted_summary_keeps_its_own_age():
    unforbid = {"id": "unforbid", "enabled": True, "last_run_hours_ago": 0.1, "summary": "idle", "acting_on": 0,
                "last_acted_hours_ago": 1.0, "last_acted_summary": "unforbade 14"}
    assert "- unforbid: unforbade 14 (acted 1h ago)" in _lines(unforbid)
