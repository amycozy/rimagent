"""notebook_write and notebook_append refuse a notebook over NOTEBOOK_BUDGET."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from rimagent import memory
from rimagent.tools import brain

pytestmark = pytest.mark.usefixtures("clean_brain")


def _ctx():
    return SimpleNamespace(emit=lambda kind, data=None: None)


def test_write_at_the_limit_is_kept():
    text = "x" * memory.NOTEBOOK_BUDGET
    assert brain.notebook_write(_ctx(), text) == f"notebook is now {memory.NOTEBOOK_BUDGET} chars"
    assert memory.notebook_read().strip() == text


def test_write_over_the_limit_is_refused_and_says_the_sizes():
    brain.notebook_write(_ctx(), "plan")
    with pytest.raises(ValueError) as info:
        brain.notebook_write(_ctx(), "y" * 259_667)
    msg = str(info.value)
    assert "259667 chars" in msg and f"limit is {memory.NOTEBOOK_BUDGET}" in msg
    assert "notebook is 5 chars" in msg
    assert memory.notebook_read() == "plan\n"


def test_append_over_the_limit_is_refused():
    brain.notebook_write(_ctx(), "a" * (memory.NOTEBOOK_BUDGET - 10))
    before = memory.notebook_read()
    with pytest.raises(ValueError) as info:
        brain.notebook_append(_ctx(), "b" * 20)
    assert f"would be {memory.NOTEBOOK_BUDGET + 12} chars" in str(info.value)
    assert memory.notebook_read() == before
    assert brain.notebook_append(_ctx(), "c" * 8) == "appended"
    assert len(memory.notebook_read().strip()) == memory.NOTEBOOK_BUDGET
