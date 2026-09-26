"""The Steward stock line names a production job's bill, who added it, and the fields the job keeps."""
from __future__ import annotations

from rimagent import loop

ROW = {"kind": "production", "label": "simple meal", "target": 22, "current": 2, "enabled": True, "designations": 0,
       "last_run_hours_ago": 1.0, "failures": 0}
BILL = {"id": "Bill_CookMealSimple_2", "table": "Campfire14732", "added_by_job": False, "next_run_in_hours": 0.4,
        "keeps": {"repeat_mode": "TargetCount", "target": 22, "suspended": False, "pause_when_satisfied": False}}


def test_line_names_the_bill_and_the_fields_it_keeps():
    line = loop.steward_stock_line(dict(ROW, bill=BILL))
    assert line.endswith("(last run 1h ago); bill Bill_CookMealSimple_2, added by job: no, "
                         "keeps repeat_mode=TargetCount target=22 suspended=false pause_when_satisfied=false")


def test_line_says_when_the_job_added_the_bill():
    assert "; bill Bill_CookMealSimple_2, added by job: yes, keeps" in loop.steward_stock_line(dict(ROW, bill=dict(BILL, added_by_job=True)))


def test_line_without_a_bill_is_unchanged():
    assert "bill" not in loop.steward_stock_line(ROW)
    assert "bill" not in loop.steward_stock_line(dict(ROW, bill=None))
