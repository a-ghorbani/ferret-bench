"""OpenAI-compatible client for llama-swap (llama.cpp). Single-GPU discipline: strictly serial,
warm-up with retries before each model's batch (cold loads are slow/flaky).
"""

import os
import time

import requests

BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:8080")
REQUEST_TIMEOUT_S = 600  # generous: cold loads + long prefills


class LLMError(Exception):
    pass


def list_models():
    r = requests.get(f"{BASE_URL}/v1/models", timeout=30)
    r.raise_for_status()
    return [m["id"] for m in r.json()["data"]]


def warm_model(model: str, retries: int = 5):
    """Tiny completion to force llama-swap to load the model; retry through cold-load flakiness."""
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(f"{BASE_URL}/v1/chat/completions", timeout=REQUEST_TIMEOUT_S, json={
                "model": model,
                "messages": [{"role": "user", "content": "Say OK."}],
                "max_tokens": 4, "temperature": 0,
            })
            if r.status_code == 200:
                return True
            last = f"HTTP {r.status_code}: {r.text[:300]}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(10 * (attempt + 1))
    raise LLMError(f"warm-up failed for {model}: {last}")


def chat(model: str, messages, tools=None, gen=None, retries: int = 3,
         base_url: str = None, api_key: str = None):
    """One chat completion (llama-swap by default; any OpenAI-compatible API via base_url/api_key).
    Returns the raw response dict. Retries transient failures."""
    payload = {"model": model, "messages": messages}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    for k, v in (gen or {}).items():
        payload[k] = v
    url = f"{base_url or BASE_URL}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_S)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:500]}"
            if r.status_code in (400, 401, 422):  # not transient — surface now
                raise LLMError(last)
        except requests.RequestException as e:
            last = str(e)
        time.sleep(5 * (attempt + 1))
    raise LLMError(f"chat failed for {model}: {last}")
