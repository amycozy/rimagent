"""An unknown tool whose rw_ form exists names that form."""
from __future__ import annotations

from rimagent.registry import Registry, tool


def test_unknown_tool_names_the_rw_form():
    reg = Registry()

    @tool("rw_ui_job", "j")
    def job(ctx):
        return 1

    reg.add(job)
    assert reg.execute(None, "ui_job", {}) == ({"error": "unknown tool 'ui_job'; 'rw_ui_job' exists"}, False)
    assert reg.execute(None, "ui_nope", {}) == ({"error": "unknown tool 'ui_nope'"}, False)
