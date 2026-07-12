"""Faithful replica of PocketPal's AgentRunner ReAct loop (CONTRACT.md §Agent loop).

Termination: first turn with no tool_calls → final; turn cap while still calling tools →
forced no-tools final with the shipped budget-exhausted nudge; errors become tool-message
content, never exceptions.
"""

import json
import random

from configs import build_system_prompt, build_tools
from llm import LLMError, chat
from talents import exec_read_url, exec_web_search

FORCED_FINAL_NUDGE = ("(Tool budget exhausted. Answer now using only the information gathered above; "
                      "if it is insufficient, say what is missing.)")

# The web_search + read_url schemas cost ~250-450 rendered tokens. A turn-1 prompt below this,
# with tools passed, means the chat template never rendered them (see report.md RQ6 correction).
SCHEMA_RENDERED_MIN_TOKENS = 300


def _normalize_tool_calls(raw, seed):
    """Backfill synthetic ids like PocketPal normalizeToolCallIds."""
    calls = []
    for i, c in enumerate(raw or []):
        fn = c.get("function") or {}
        calls.append({
            "id": c.get("id") or f"call_{seed}_{i}",
            "type": "function",
            "function": {"name": fn.get("name") or "", "arguments": fn.get("arguments") or "{}"},
        })
    return calls


def _execute_one(call, cfg, rng, http_mode, anchor_date, telemetry):
    name = call["function"]["name"]
    allowed = {"web_search"} | ({"read_url"} if cfg["read_url_policy"] != "disabled" else set())
    if not name:
        return "Unknown talent (no function name)", False
    if name not in allowed:
        return f'Talent "{name}" is not enabled for this Pal', False
    try:
        args = json.loads(call["function"]["arguments"] or "{}")
        if not isinstance(args, dict):
            raise ValueError("args not an object")
    except (json.JSONDecodeError, ValueError):
        return f"Error: invalid JSON arguments for {name}", False
    try:
        if name == "web_search":
            return exec_web_search(args, cfg, rng, http_mode, anchor_date, telemetry), True
        return exec_read_url(args, cfg, rng, http_mode, telemetry), True
    except Exception as e:  # handler throw → error string, loop continues (contract)
        return f"Error executing {name}: {e}", True


def run_agent(question: str, model: str, cfg: dict, anchor_date: str, http_mode: str, seed: int = 0):
    """Run one question through the loop. Returns a full record for outputs.jsonl."""
    rng = random.Random(seed)
    tools = build_tools(cfg)
    messages = [
        {"role": "system", "content": build_system_prompt(cfg, anchor_date)},
        {"role": "user", "content": question},
    ]
    telemetry = {}
    schema_not_rendered = False
    turns, tool_call_log, usage_total = [], [], {"prompt_tokens": 0, "completion_tokens": 0}
    final_answer, hit_max_turns, force_final, error = None, False, False, None
    turn = 0

    while turn < cfg["max_turns"] or force_final:
        turn_tools = None if (force_final or not tools) else tools
        try:
            resp = chat(model, messages, tools=turn_tools, gen=cfg["gen"])
        except LLMError as e:
            error = str(e)
            break
        msg = (resp.get("choices") or [{}])[0].get("message") or {}
        usage = resp.get("usage") or {}
        usage_total["prompt_tokens"] += usage.get("prompt_tokens", 0)
        usage_total["completion_tokens"] += usage.get("completion_tokens", 0)

        # CANARY: if we passed tools but the runtime rendered a prompt too short to contain the
        # schemas, the model's chat template silently dropped them — it was never offered the tools.
        # Five models failed this way and we misread it as them refusing to comply. Never again.
        if turn == 0 and turn_tools and usage.get("prompt_tokens"):
            if usage["prompt_tokens"] < SCHEMA_RENDERED_MIN_TOKENS:
                schema_not_rendered = True
        content = msg.get("content") or ""
        raw_calls = msg.get("tool_calls") or []
        calls = _normalize_tool_calls(raw_calls, seed=f"{seed}_{turn}")
        turns.append({"turn": turn, "content": content, "n_tool_calls": len(calls),
                      "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                      "forced_final": force_final})

        if force_final or not calls:
            final_answer = content
            break

        assistant_msg = {"role": "assistant", "content": content, "tool_calls": calls}
        tool_msgs = []
        for call in calls:
            result, arg_valid = _execute_one(call, cfg, rng, http_mode, anchor_date, telemetry)
            tool_call_log.append({"turn": turn, "name": call["function"]["name"],
                                  "arguments": call["function"]["arguments"],
                                  "args_valid": arg_valid, "result_chars": len(result)})
            tool_msgs.append({"role": "tool", "tool_call_id": call["id"], "content": result})
        messages = messages + [assistant_msg] + tool_msgs
        turn += 1

        if turn >= cfg["max_turns"]:
            hit_max_turns = True
            force_final = True
            messages = messages + [{"role": "user", "content": FORCED_FINAL_NUDGE}]

    return {
        "final_answer": final_answer,
        "error": error,
        "turns": turns,
        "n_turns": len(turns),
        "hit_max_turns": hit_max_turns,
        "tool_calls": tool_call_log,
        "schema_not_rendered": schema_not_rendered,  # tools passed but template dropped them
        "n_searches": len(telemetry.get("searches", [])),
        "n_reads": len(telemetry.get("reads", [])),
        "telemetry": telemetry,
        "usage": usage_total,
        "messages": messages if final_answer is None else messages + [{"role": "assistant", "content": final_answer}],
    }
