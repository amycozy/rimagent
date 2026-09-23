"""The combat order's state line in the Steward block, with nobody drafted."""
from __future__ import annotations

from rimagent import loop

ENGAGED = ("engaged: 1 hostile(s), 0 drafted (holding rally), 0 restricted to Home; "
           "1 of 1 ranged fighters can hit Avro (7 cells)")


def _status(combat):
    return {"orders": [combat, {"id": "rescue", "enabled": True, "summary": "nobody downed", "acting_on": 0}], "rally": [40, 40, 6, 6]}


def test_engaged_with_nobody_drafted_prints_the_state():
    combat = {"id": "combat", "enabled": True, "summary": ENGAGED, "acting_on": 0, "state": ENGAGED}
    assert f"- combat: {ENGAGED}" in loop.steward_orders_lines(_status(combat), 3, 2.0)


def test_long_state_is_not_cut_at_the_summary_length():
    long = ENGAGED + "; watching: 3 hostile(s) not engaging (2 staging at 80 cells, 1 sleeping at 120 cells)"
    assert len(long) > 140
    combat = {"id": "combat", "enabled": True, "summary": long, "acting_on": 0, "state": long}
    assert f"- combat: {long}" in loop.steward_orders_lines(_status(combat), 3, 2.0)


def test_state_equal_to_the_summary_is_printed_once_when_acting():
    long = ENGAGED + "; watching: 3 hostile(s) not engaging (2 staging at 80 cells, 1 sleeping at 120 cells)"
    combat = {"id": "combat", "enabled": True, "summary": long, "acting_on": 2, "state": long}
    assert f"- combat: {long} (acting on 2)" in loop.steward_orders_lines(_status(combat), 3, 2.0)
