"""journal_append reports an entry already recorded under the same title."""
from __future__ import annotations

from types import SimpleNamespace

from rimagent import memory
from rimagent.tools.brain import journal_append


def test_same_title_is_reported_and_not_appended(tmp_path, monkeypatch):
    journal = tmp_path / "journal.md"
    monkeypatch.setattr(memory, "JOURNAL", journal)
    ctx = SimpleNamespace(episode=2, emit=lambda kind, data: None)
    assert journal_append(ctx, "Spike traps hit colonists at door gaps.", title="Spike traps: door gaps") == "recorded"
    stamp = memory.journal_recorded("Spike traps: door gaps")
    assert stamp and stamp.endswith(" (episode 2)")
    before = journal.read_text(encoding="utf-8")
    assert journal_append(ctx, "Again.", title="Spike traps: door gaps") == f"already recorded {stamp} under this title; not appended"
    assert journal.read_text(encoding="utf-8") == before
    assert journal_append(ctx, "Other.", title="Spike traps") == "recorded"
