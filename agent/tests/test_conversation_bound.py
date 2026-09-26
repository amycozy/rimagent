"""The conversation bound counts tool-call arguments, and a context-window error shortens the retry."""
from __future__ import annotations

import json
from types import SimpleNamespace

from rimagent import loop
from rimagent.context import WakePlan
from rimagent.llm import LLM, LLMReply


def _call(cid, name, args):
    return {"id": cid, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


def test_message_chars_counts_arguments():
    m = {"role": "assistant", "content": "ab", "tool_calls": [_call("1", "notebook_write", {"text": "x" * 100})]}
    assert loop.message_chars(m) == 2 + len(json.dumps({"text": "x" * 100}))


def test_bound_shortens_long_arguments_and_keeps_json():
    big = "line\n" * 60_000
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"},
            {"role": "assistant", "content": "", "tool_calls": [_call("1", "notebook_write", {"text": big, "n": 3})]},
            {"role": "tool", "tool_call_id": "1", "content": "notebook is now 300000 chars"}]
    before, after = loop.bound_messages(msgs)
    assert before > loop.BOUND_HIGH and after < loop.BOUND_LOW
    args = json.loads(msgs[2]["tool_calls"][0]["function"]["arguments"])
    assert args["n"] == 3
    assert args["text"].startswith("line\n") and "elided" in args["text"]


def test_bound_leaves_a_small_conversation_alone():
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}, {"role": "tool", "content": "z" * 1000}]
    loop.bound_messages(msgs)
    assert msgs[2]["content"] == "z" * 1000


class FakeLLM:
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    def chat(self, messages, tools, **kw):
        self.seen.append(json.loads(json.dumps(messages)))
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    assistant_message = LLM.assistant_message


class FakeRegistry:
    def reload_brain(self):
        pass

    def specs(self, **kw):
        return [{"function": {"name": n}} for n in ("notebook_write", "end_turn")]

    def execute(self, ctx, name, args):
        if name == "end_turn":
            ctx.stop_turn = True
        return "ok", True


def test_context_overflow_retries_with_a_shorter_conversation():
    big = "x" * 100_000
    llm = FakeLLM([
        LLMReply(tool_calls=[{"id": "1", "name": "notebook_write", "arguments": {"text": big}}]),
        RuntimeError("The input (262181 tokens) is longer than the model's context length (262144 tokens)."),
        LLMReply(tool_calls=[{"id": "2", "name": "end_turn", "arguments": {}}]),
    ])
    events = []
    ctx = SimpleNamespace(config={"play": {}}, registry=FakeRegistry(), llm=llm, stream="play", episode=1, seed="s",
                          extra={}, interrupt_check=None, stop_turn=False, wake=WakePlan(), end_episode_reason=None,
                          emit=lambda kind, data: events.append((kind, data)))
    ctx.reset_turn = lambda: None
    res = loop.think(ctx, "go", system="sys")
    assert res.ended_by_tool
    failed, retried = llm.seen[1], llm.seen[2]
    size = lambda msgs: sum(loop.message_chars(m) for m in msgs)
    assert size(retried) <= size(failed) // 2
    assert any("context window exceeded" in d.get("text", "") for k, d in events if k == "log")
