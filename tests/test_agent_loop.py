"""Agent-loop termination paths and the two canaries.

Both published retractions were harness bugs in this file's behaviour, not model behaviour:
the schema-not-rendered canary (five models never received the tools) and the
answer-from-reasoning canary (thinking models' answers were discarded). These tests pin
both, plus every way the loop can terminate. No network: chat() is stubbed.
"""
import unittest
from unittest import mock

from _harness_path import agent_loop, configs  # noqa: E402


def _resp(content="", tool_calls=None, prompt_tokens=500, completion_tokens=10, reasoning=None):
    msg = {"content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    if reasoning is not None:
        msg["reasoning_content"] = reasoning
    return {"choices": [{"message": msg}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}}


def _call(name="web_search", args='{"query":"x"}', cid="c1"):
    return {"id": cid, "type": "function", "function": {"name": name, "arguments": args}}


CFG = configs.load_config("frozen")


class TestTermination(unittest.TestCase):
    def test_no_tool_calls_terminates_immediately_with_content(self):
        with mock.patch.object(agent_loop, "chat", return_value=_resp("the answer")) as c:
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertEqual(rec["final_answer"], "the answer")
        self.assertEqual(rec["n_turns"], 1)
        self.assertFalse(rec["hit_max_turns"])
        self.assertEqual(c.call_count, 1)

    def test_tool_call_then_answer_is_two_turns(self):
        responses = [_resp("", [_call()]), _resp("final")]
        with mock.patch.object(agent_loop, "chat", side_effect=responses), \
             mock.patch.object(agent_loop, "exec_web_search", return_value="RESULTS"):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertEqual(rec["final_answer"], "final")
        self.assertEqual(rec["n_turns"], 2)
        self.assertEqual(len(rec["tool_calls"]), 1)
        self.assertEqual(rec["tool_calls"][0]["name"], "web_search")

    def test_n_searches_counts_executed_provider_calls_not_attempts(self):
        """n_searches = len(telemetry["searches"]), written inside exec_web_search — NOT the
        number of tool calls the model emitted. Every search-rate figure in this project
        (search propensity, false-search rate) is therefore "reached the provider", not
        "the model tried". A call that fails argument validation never counts."""
        with mock.patch.object(agent_loop, "chat",
                               side_effect=[_resp("", [_call(args="{bad")]), _resp("ok")]):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertEqual(len(rec["tool_calls"]), 1, "the model did emit a tool call")
        self.assertEqual(rec["n_searches"], 0, "but it never reached the provider")

    def test_turn_cap_forces_a_final_answer(self):
        """Model keeps calling tools; loop must stop and force one last tool-free turn."""
        always_tool = _resp("", [_call()])
        with mock.patch.object(agent_loop, "chat",
                               side_effect=[always_tool] * CFG["max_turns"] + [_resp("forced")]), \
             mock.patch.object(agent_loop, "exec_web_search", return_value="RESULTS"):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertTrue(rec["hit_max_turns"])
        self.assertEqual(rec["final_answer"], "forced")
        self.assertTrue(rec["turns"][-1]["forced_final"],
                        "the last turn must be flagged forced_final")

    def test_forced_final_turn_is_sent_without_tools(self):
        seen = []

        def spy(model, messages, tools=None, gen=None):
            seen.append(tools)
            return _resp("", [_call()]) if len(seen) <= CFG["max_turns"] else _resp("done")

        with mock.patch.object(agent_loop, "chat", side_effect=spy), \
             mock.patch.object(agent_loop, "exec_web_search", return_value="R"):
            agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertIsNotNone(seen[0], "normal turns must offer tools")
        self.assertIsNone(seen[-1], "the forced-final turn must withhold tools")

    def test_llm_error_records_error_and_stops(self):
        with mock.patch.object(agent_loop, "chat", side_effect=agent_loop.LLMError("boom")):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertIn("boom", rec["error"])
        self.assertIsNone(rec["final_answer"])


class TestToolErrorHandling(unittest.TestCase):
    def test_handler_throw_becomes_a_tool_message_and_loop_continues(self):
        """A failing tool must not kill the item — it returns an error string the model can read."""
        with mock.patch.object(agent_loop, "chat",
                               side_effect=[_resp("", [_call()]), _resp("recovered")]), \
             mock.patch.object(agent_loop, "exec_web_search", side_effect=RuntimeError("provider down")):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertEqual(rec["final_answer"], "recovered")
        self.assertIsNone(rec["error"])
        tool_msgs = [m for m in rec["messages"] if m.get("role") == "tool"]
        self.assertIn("provider down", tool_msgs[0]["content"])

    def test_invalid_json_arguments_are_flagged_not_crashed(self):
        with mock.patch.object(agent_loop, "chat",
                               side_effect=[_resp("", [_call(args="{not json")]), _resp("ok")]):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertFalse(rec["tool_calls"][0]["args_valid"])
        self.assertEqual(rec["final_answer"], "ok")

    def test_disabled_tool_is_refused(self):
        cfg = configs.load_config("frozen-readoff")  # read_url disabled
        with mock.patch.object(agent_loop, "chat",
                               side_effect=[_resp("", [_call(name="read_url", args='{"url":"u"}')]),
                                            _resp("ok")]):
            rec = agent_loop.run_agent("q?", "m", cfg, "2026-07-22", "replay-only")
        tool_msgs = [m for m in rec["messages"] if m.get("role") == "tool"]
        self.assertIn("not enabled", tool_msgs[0]["content"])
        self.assertEqual(rec["n_reads"], 0)


class TestCanaries(unittest.TestCase):
    def test_schema_not_rendered_fires_on_short_first_prompt(self):
        """Five models silently never received the tool schema; this is the detector."""
        short = agent_loop.SCHEMA_RENDERED_MIN_TOKENS - 1
        with mock.patch.object(agent_loop, "chat", return_value=_resp("a", prompt_tokens=short)):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertTrue(rec["schema_not_rendered"])

    def test_schema_canary_silent_when_prompt_is_long_enough(self):
        long = agent_loop.SCHEMA_RENDERED_MIN_TOKENS + 1
        with mock.patch.object(agent_loop, "chat", return_value=_resp("a", prompt_tokens=long)):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertFalse(rec["schema_not_rendered"])

    def test_answer_in_reasoning_block_is_used_and_flagged(self):
        """llama.cpp can route the whole answer to reasoning_content; discarding it
        penalised thinking models and produced a retracted leaderboard claim."""
        with mock.patch.object(agent_loop, "chat",
                               return_value=_resp("", reasoning="the real answer")):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertEqual(rec["final_answer"], "the real answer")
        self.assertTrue(rec["answer_from_reasoning"])

    def test_visible_content_wins_over_reasoning(self):
        with mock.patch.object(agent_loop, "chat",
                               return_value=_resp("visible", reasoning="hidden")):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertEqual(rec["final_answer"], "visible")
        self.assertFalse(rec["answer_from_reasoning"])

    def test_empty_turn_with_tokens_spent_is_counted(self):
        with mock.patch.object(agent_loop, "chat",
                               return_value=_resp("", completion_tokens=42)):
            rec = agent_loop.run_agent("q?", "m", CFG, "2026-07-22", "replay-only")
        self.assertEqual(rec["empty_content_turns"], 1)


class TestToolCallIdBackfill(unittest.TestCase):
    def test_missing_id_is_backfilled_deterministically(self):
        raw = [{"function": {"name": "web_search", "arguments": "{}"}}]
        a = agent_loop._normalize_tool_calls(raw, seed="7_0")
        b = agent_loop._normalize_tool_calls(raw, seed="7_0")
        self.assertEqual(a[0]["id"], b[0]["id"])
        self.assertTrue(a[0]["id"].startswith("call_7_0"))

    def test_existing_id_is_preserved(self):
        raw = [{"id": "abc", "function": {"name": "web_search", "arguments": "{}"}}]
        self.assertEqual(agent_loop._normalize_tool_calls(raw, seed="1_0")[0]["id"], "abc")


if __name__ == "__main__":
    unittest.main()
