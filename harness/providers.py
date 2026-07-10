"""Search providers + page reader, replicating PocketPal's adapters (see CONTRACT.md §Providers).

Normalized hit: {title, url, snippet, publishedAt?}. All HTTP goes through the record-replay cache.
"""

import json
import os
import urllib.parse

from http_cache import cached_request


class ProviderError(Exception):
    pass


def _require_key(env_var: str, provider: str) -> str:
    key = os.environ.get(env_var, "").strip()
    if not key:
        raise ProviderError(f"{provider} key not set")
    return key


def tavily_search(query: str, max_results: int, mode: str):
    key = _require_key("TAVILY_API_KEY", "Tavily")
    body = {"api_key": key, "query": query, "max_results": max_results, "search_depth": "basic"}
    res = cached_request("tavily", "POST", "https://api.tavily.com/search", json_body=body, mode=mode)
    if res["status"] < 200 or res["status"] >= 300:
        raise ProviderError(f"request failed ({res['status']})")
    data = json.loads(res["text"])
    hits = []
    for r in data.get("results", []):
        hits.append({"title": r.get("title") or "", "url": r.get("url") or "",
                     "snippet": r.get("content") or "", "publishedAt": r.get("published_date")})
    return hits, res


def brave_search(query: str, max_results: int, mode: str):
    key = _require_key("BRAVE_API_KEY", "Brave")
    url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count={max_results}"
    res = cached_request("brave", "GET", url, mode=mode,
                         headers={"X-Subscription-Token": key, "Accept": "application/json"})
    if res["status"] < 200 or res["status"] >= 300:
        raise ProviderError(f"request failed ({res['status']})")
    data = json.loads(res["text"])
    hits = []
    for r in (data.get("web") or {}).get("results", []):
        hits.append({"title": r.get("title") or "", "url": r.get("url") or "",
                     "snippet": r.get("description") or "", "publishedAt": r.get("page_age")})
    return hits, res


SEARCH_PROVIDERS = {"tavily": tavily_search, "brave": brave_search}


def search(provider: str, query: str, max_results: int, mode: str):
    if provider not in SEARCH_PROVIDERS:
        raise ProviderError(f"unknown provider {provider}")
    return SEARCH_PROVIDERS[provider](query, max_results, mode)


def read_page(url: str, mode: str):
    """Default reader = r.jina.ai (keyless), as in PocketPal's readWithDefaultReader."""
    reader_url = "https://r.jina.ai/" + urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%")
    res = cached_request("jina-reader", "GET", reader_url, mode=mode, timeout=30)
    if res["status"] < 200 or res["status"] >= 300:
        raise ProviderError(f"request failed ({res['status']})")
    return {"url": url, "text": res["text"]}, res
