"""run_python: the examples in its description parse, and a SyntaxError names its line."""
from __future__ import annotations

import ast
from types import SimpleNamespace

import pytest

from rimagent.tools import meta


@pytest.mark.parametrize("example", ['find("Bed")', 'rpc("defs.get", **{"def": "Bed"})'])
def test_description_examples_parse(example):
    doc = meta.run_python._tool_desc
    assert example.replace('"', '\\"') in doc or example in doc
    ast.parse(example)
    assert "find(def=" not in doc


def test_syntax_error_gives_line_offset_and_text():
    with pytest.raises(SyntaxError) as info:
        meta.run_python(SimpleNamespace(bridge=None), "x = 1\nbeds = find(def='Bed')\n")
    text = str(info.value)
    assert "at line 2, offset" in text
    assert text.endswith("beds = find(def='Bed')")
