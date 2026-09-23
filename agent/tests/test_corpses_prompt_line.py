"""The system prompt states what the corpses order never does with a human corpse."""
from __future__ import annotations

from rimagent import loop


def test_corpses_line_names_the_human_corpse_limits():
    text = (loop.PROMPTS / "system.md").read_text(encoding="utf-8")
    assert "it never butchers a human corpse" in text
    assert "does nothing with a human corpse when there is no free grave, no stockpile that accepts the corpse and no work table with the cremation recipe" in text
