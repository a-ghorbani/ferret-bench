"""Record-replay cache for all external HTTP (search providers + page reader).

Cache keys and stored records NEVER contain API keys: the canonical request is
built from provider name + method + key-stripped URL + key-stripped body.

Modes:
  replay-or-live (default): use cache if present, else hit network and record.
  replay-only: cache miss is an error (strict comparability runs).
  live: always hit network and overwrite the record (dataset refresh).
"""

import json
import time
from pathlib import Path

import requests

from common import REPO_DIR, canonical_json, sha256_text

CACHE_DIR = REPO_DIR / "cache" / "http"
DEFAULT_TIMEOUT_S = 12  # PocketPal DEFAULT_TIMEOUT_MS = 12000
MAX_BODY_BYTES = 2 * 1024 * 1024  # PocketPal MAX_BODY_BYTES

SECRET_FIELDS = {"api_key", "apikey", "key", "token"}
SECRET_HEADERS = {"x-subscription-token", "x-api-key", "authorization"}


class CacheMiss(Exception):
    pass


def _strip_secrets_body(body):
    if isinstance(body, dict):
        return {k: ("<redacted>" if k.lower() in SECRET_FIELDS else _strip_secrets_body(v)) for k, v in body.items()}
    if isinstance(body, list):
        return [_strip_secrets_body(v) for v in body]
    return body


def cache_key(provider: str, method: str, url: str, body) -> str:
    canon = canonical_json({
        "provider": provider,
        "method": method.upper(),
        "url": url,  # callers must pass key-free URLs (keys go in headers/body only)
        "body": _strip_secrets_body(body) if body is not None else None,
    })
    return sha256_text(canon)


def _cache_path(key: str) -> Path:
    return CACHE_DIR / key[:2] / f"{key}.json"


def cached_request(provider: str, method: str, url: str, *, headers=None, json_body=None,
                   mode: str = "replay-or-live", timeout=DEFAULT_TIMEOUT_S):
    """Returns dict: {status, text, from_cache, captured_at}. Raises CacheMiss in replay-only mode."""
    assert mode in ("replay-or-live", "replay-only", "live"), mode
    key = cache_key(provider, method, url, json_body)
    path = _cache_path(key)

    if mode != "live" and path.is_file():
        rec = json.loads(path.read_text())
        return {"status": rec["status"], "text": rec["text"], "from_cache": True,
                "captured_at": rec["captured_at"], "cache_key": key}

    if mode == "replay-only":
        raise CacheMiss(f"{provider} {method} {url} not in replay cache")

    resp = requests.request(method, url, headers=headers or {}, json=json_body, timeout=timeout)
    text = resp.text[:MAX_BODY_BYTES]
    rec = {
        "provider": provider,
        "method": method.upper(),
        "url": url,
        "body": _strip_secrets_body(json_body) if json_body is not None else None,
        "status": resp.status_code,
        "text": text,
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, ensure_ascii=False))
    return {"status": resp.status_code, "text": text, "from_cache": False,
            "captured_at": rec["captured_at"], "cache_key": key}
