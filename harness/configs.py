"""Config schema, tool definitions, and system-prompt variants.

A config is a flat dict of factor levels (see factors.md); `shipped.json` reproduces PocketPal
PR #808 exactly (see CONTRACT.md). Config identity = sha256 of its canonical JSON.
"""

import json
from pathlib import Path

from common import HARNESS_DIR, canonical_json, sha256_text

CONFIG_DIR = HARNESS_DIR / "configs"

SHIPPED_DEFAULTS = {
    "config_id": None,               # human name; hash is authoritative
    "tools_enabled": True,            # False = floor baseline (no tools at all)
    "provider": "tavily",
    "result_count": 5,
    "result_format": "shipped",       # shipped | compact | markdown | json
    "snippet_chars": 280,
    "menu_token_ceiling": 1000,
    "read_url_policy": "available",   # disabled | available | encouraged
    "read_content_chars": 4800,
    "max_turns": 5,
    "system_prompt": "shipped",       # date-only | shipped | guided
    "tool_desc": "shipped",           # shipped | enriched
    "untrusted_wrapper": True,
    "enable_thinking": False,   # FACTOR. Off = all models comparable + phone-realistic token cost.
                                # Thinking-capable models otherwise burn a large reasoning budget
                                # inside a loop already full of search results (see report.md).
    "gen": {"temperature": 0.7, "top_p": 0.95, "max_tokens": 1024, "seed": 42},
}


def load_config(name_or_path: str) -> dict:
    p = Path(name_or_path)
    if not p.is_file():
        p = CONFIG_DIR / f"{name_or_path}.json"
    cfg = {**SHIPPED_DEFAULTS, **json.loads(p.read_text())}
    cfg["config_hash"] = sha256_text(canonical_json({k: v for k, v in cfg.items() if k not in ("config_id", "config_hash")}))
    return cfg


# --- Tool definitions (descriptions are a factor; 'shipped' verbatim per CONTRACT.md) ---

TOOL_DESCS = {
    "shipped": {
        "web_search": ("Search the web for current information on any topic. Use for news, facts, or data "
                       "beyond your knowledge cutoff. Returns result titles, source URLs, and snippets."),
        "web_search.query": "The search query.",
        "read_url": ("Open one web page and read its content. Use after web_search when a snippet is not "
                     "enough to answer. Provide an exact URL, usually from web_search results."),
        "read_url.url": "The URL of the page to read.",
    },
    "enriched": {
        "web_search": ("Search the web for current information. Use this for any question about news, current "
                       "events, prices, releases, sports, weather, or any fact that may have changed since your "
                       "training data or that you are unsure about. Write short keyword queries (2-6 words), like "
                       "a search engine user, not full sentences. Returns result titles, source URLs, and text snippets."),
        "web_search.query": "Short keyword search query, e.g. 'nobel prize physics 2026 winner'.",
        "read_url": ("Fetch the full text of one web page. Use this after web_search when a snippet mentions the "
                     "answer but does not fully contain it. Pass the exact URL copied from a web_search result. "
                     "Do not invent URLs."),
        "read_url.url": "Exact URL copied from a web_search result.",
    },
    # --- Trigger-clause test (PREREG-2026-07-21). Arms B1/B2 differ from 'enriched' ONLY in the
    # tail of web_search's description — the clause that decides WHEN to search. Everything else
    # (topic list, query-style guidance, return description, both read_url strings) is byte-identical
    # to 'enriched', so tool_desc is a genuine single factor across the three arms.
    #
    # 'enriched' tail (control):  "...or any fact that may have changed since your training data
    #                              or that you are unsure about."  <- cutoff-referential + self-referential
    "no-cutoff": {  # B1: drop the training-cutoff reference, KEEP the uncertainty trigger
        "web_search": ("Search the web for current information. Use this for any question about news, current "
                       "events, prices, releases, sports, weather, or any fact that you are unsure about. "
                       "Write short keyword queries (2-6 words), like "
                       "a search engine user, not full sentences. Returns result titles, source URLs, and text snippets."),
        "web_search.query": "Short keyword search query, e.g. 'nobel prize physics 2026 winner'.",
        "read_url": ("Fetch the full text of one web page. Use this after web_search when a snippet mentions the "
                     "answer but does not fully contain it. Pass the exact URL copied from a web_search result. "
                     "Do not invent URLs."),
        "read_url.url": "Exact URL copied from a web_search result.",
    },
    "parallel": {  # B2: no cutoff reference; volatility trigger sits BESIDE uncertainty, not instead of it
        "web_search": ("Search the web for current information. Use this for any question about news, current "
                       "events, prices, releases, sports, weather, any fact whose answer can change over time, "
                       "or anything you are unsure about. Write short keyword queries (2-6 words), like "
                       "a search engine user, not full sentences. Returns result titles, source URLs, and text snippets."),
        "web_search.query": "Short keyword search query, e.g. 'nobel prize physics 2026 winner'.",
        "read_url": ("Fetch the full text of one web page. Use this after web_search when a snippet mentions the "
                     "answer but does not fully contain it. Pass the exact URL copied from a web_search result. "
                     "Do not invent URLs."),
        "read_url.url": "Exact URL copied from a web_search result.",
    },
}


def build_tools(cfg: dict):
    if not cfg["tools_enabled"]:
        return None
    d = TOOL_DESCS[cfg["tool_desc"]]
    tools = [{
        "type": "function",
        "function": {
            "name": "web_search",
            "description": d["web_search"],
            "parameters": {"type": "object",
                           "properties": {"query": {"type": "string", "description": d["web_search.query"]}},
                           "required": ["query"]},
        },
    }]
    if cfg["read_url_policy"] != "disabled":
        tools.append({
            "type": "function",
            "function": {
                "name": "read_url",
                "description": d["read_url"],
                "parameters": {"type": "object",
                               "properties": {"url": {"type": "string", "description": d["read_url.url"]}},
                               "required": ["url"]},
            },
        })
    return tools


# --- System prompt variants (grounding line is a factor; 'shipped' verbatim per CONTRACT.md) ---

BASE_SYSTEM = "You are a helpful assistant."


def build_system_prompt(cfg: dict, anchor_date: str) -> str:
    if not cfg["tools_enabled"]:
        return f"{BASE_SYSTEM} Today's date is {anchor_date}. Answer from your own knowledge, concisely."
    budget = cfg["max_turns"] - 1
    has_read = cfg["read_url_policy"] != "disabled"
    variant = cfg["system_prompt"]
    if variant == "bare":
        # NO date, no guidance — just the assistant line. The counterfactual we never ran:
        # every other variant contained the date, so the date's own effect was never isolated.
        return BASE_SYSTEM
    if variant == "date-only":
        return f"{BASE_SYSTEM} Today's date is {anchor_date}."
    if variant == "shipped":
        open_pages = " and open pages with read_url" if has_read else ""
        line = (f"Today's date is {anchor_date}. You can search the web with web_search{open_pages}. "
                f"For time-sensitive or factual questions, search first; usually one or two searches suffice — "
                f"you have a budget of {budget} tool calls. Answer using the facts in the results and cite "
                "source URLs. If the results do not contain the answer, say so rather than guessing.")
        if cfg["read_url_policy"] == "encouraged" and has_read:
            line += " When snippets are not enough, open the best result with read_url before answering."
        return f"{BASE_SYSTEM}\n{line}"
    if variant == "guided-v2":
        # guided strategy + explicit no-search escape hatch (screening showed plain 'guided'
        # causes false searches on ~29% of no_search questions)
        steps = [
            "(1) If the question is about facts, news, or anything possibly beyond your training data, call "
            "web_search first — write a short keyword query, not a full sentence.",
        ]
        if has_read:
            steps.append("(2) If the snippets do not fully answer, call read_url on the most promising result URL.")
            steps.append("(3) Answer concisely using only the retrieved facts, citing source URLs.")
        else:
            steps.append("(2) Answer concisely using only the retrieved facts, citing source URLs.")
        line = (f"Today's date is {anchor_date}. You are connected to live web search. Strategy: "
                + " ".join(steps)
                + f" You have a budget of {budget} tool calls. If the evidence does not contain the answer, "
                "say so — never guess. For creative requests, math, writing help, or general knowledge you "
                "are confident about, just answer directly without searching.")
        return f"{BASE_SYSTEM}\n{line}"
    if variant == "guided":
        steps = [
            "(1) For any question about facts, news, or anything possibly beyond your training data, call "
            "web_search first — write a short keyword query, not a full sentence.",
        ]
        if has_read:
            steps.append("(2) If the snippets do not fully answer, call read_url on the most promising result URL.")
            steps.append("(3) Answer concisely using only the retrieved facts, citing source URLs.")
        else:
            steps.append("(2) Answer concisely using only the retrieved facts, citing source URLs.")
        line = (f"Today's date is {anchor_date}. You are connected to live web search. Strategy: "
                + " ".join(steps)
                + f" You have a budget of {budget} tool calls. If the evidence does not contain the answer, "
                "say so — never guess.")
        return f"{BASE_SYSTEM}\n{line}"
    raise ValueError(f"unknown system_prompt {variant}")
