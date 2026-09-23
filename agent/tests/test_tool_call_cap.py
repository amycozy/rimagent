"""max_tool_calls holds inside one reply: calls past the cap are not run."""
from __future__ import annotations

from types import SimpleNamespace

from rimagent import loop
from rimagent.context import WakePlan
from rimagent.llm import LLM, LLMReply


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)

    def chat(self, messages, tools, **kw):
        return self.replies.pop(0)

    assistant_message = LLM.assistant_message


class FakeRegistry:
    def __init__(self):
        self.ran = []

    def reload_brain(self):
        pass

    def specs(self, **kw):
        return [{"function": {"name": n}} for n in ("look", "end_turn")]

    def execute(self, ctx, name, args):
        self.ran.append(name)
        if name == "end_turn":
            ctx.stop_turn = True
        return "ok", True


def test_calls_past_the_cap_in_one_reply_are_not_run():
    reg = FakeRegistry()
    llm = FakeLLM([
        LLMReply(tool_calls=[{"id": str(i), "name": "look", "arguments": {}} for i in range(5)]),
        LLMReply(tool_calls=[{"id": "e", "name": "end_turn", "arguments": {}}]),
    ])
    events = []
    ctx = SimpleNamespace(config={"play": {}}, registry=reg, llm=llm, stream="play", episode=1, seed="s",
                          extra={}, interrupt_check=None, stop_turn=False, wake=WakePlan(), end_episode_reason=None,
                          emit=lambda kind, data: events.append((kind, data)))
    ctx.reset_turn = lambda: None
    res = loop.think(ctx, "go", system="sys", max_calls=3)
    assert reg.ran == ["look", "look", "look", "end_turn"]
    assert res.calls == 4 and res.ended_by_tool
    skipped = [d for k, d in events if k == "tool_result" and not d["ok"]]
    assert [d["id"] for d in skipped] == ["3", "4"]
    assert skipped[0]["text"] == "not run: this step has used its 3 tool calls"
