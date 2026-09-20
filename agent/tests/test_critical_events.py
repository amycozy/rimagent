"""Which ledger events are allowed to interrupt a think step.

Episode 1, day 5: a raid began and ended inside a single 149-second inference.
The cat was killed, a colonist was wounded and the raider was downed while the
model was reasoning about wall frames. Only `critical_kinds` interrupt a step,
they match on the event's *kind*, and combat engagement is emitted under kind
"orders" -- which runner.py explicitly discards from the critical set. So the
one thing that should have stopped the step could not.

These pin the sub-kind granularity: kind "orders" stays non-interrupting in
general (rescue, corpses, fire are ordinary wakes) while combat_engaged, which
means shots are being fired right now, interrupts.
"""
from __future__ import annotations

from rimagent.runner import is_critical

KINDS = {"dialog", "danger", "manhunter", "hostile_group", "colonist_downed", "colonist_died", "mental_break", "building_lost"}
EVENTS = {"combat_engaged"}


def test_plain_critical_kind_interrupts():
    assert is_critical({"kind": "danger", "text": "danger None -> Low"}, KINDS, EVENTS)


def test_ordinary_kind_does_not_interrupt():
    assert not is_critical({"kind": "steward", "text": "stock reached"}, KINDS, EVENTS)


def test_combat_engaged_interrupts_although_its_kind_is_orders():
    e = {"kind": "orders", "text": "combat_engaged 2 hostiles, 3 drafted", "data": {"event": "combat_engaged"}}
    assert is_critical(e, KINDS, EVENTS)


def test_other_order_events_still_do_not_interrupt():
    for ev in ("combat_released", "rescue", "fire", "corpses"):
        e = {"kind": "orders", "text": f"{ev} something", "data": {"event": ev}}
        assert not is_critical(e, KINDS, EVENTS), ev


def test_order_event_without_data_falls_back_to_the_text_prefix():
    """StewardLedger.Orders writes "<event> <detail>" into text as well as data.event;
    a ledger row that lost its data payload must still be classified."""
    assert is_critical({"kind": "orders", "text": "combat_engaged 2 hostiles, 3 drafted"}, KINDS, EVENTS)


def test_unknown_event_is_not_critical():
    assert not is_critical({"kind": "orders", "text": ""}, KINDS, EVENTS)
    assert not is_critical({}, KINDS, EVENTS)
