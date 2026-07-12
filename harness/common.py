"""Shared utilities: env loading, hashing, text budgeting (replicates PocketPal searchBudget.ts)."""

import hashlib
import json
import os
import re
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
REPO_DIR = HARNESS_DIR.parent

CHARS_PER_TOKEN = 4  # PocketPal searchBudget.ts


def load_env(paths=None):
    """Load KEY=VALUE lines from the first existing .env; env vars already set win.

    Looks in the repo root, or wherever FERRET_ENV points.
    """
    candidates = paths or [p for p in (os.environ.get("FERRET_ENV"), REPO_DIR / ".env") if p]
    for p in candidates:
        if Path(p).is_file():
            for line in Path(p).read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k.startswith("export "):
                    k = k[len("export "):].strip()
                os.environ.setdefault(k, v)
            return str(p)
    return None


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def estimate_tokens(text: str) -> int:
    """PocketPal estimate: ceil(chars / 4)."""
    return -(-len(text) // CHARS_PER_TOKEN)


_TAG_RE = re.compile(r"<[^>]*>")
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_EMPH_RE = re.compile(r"[*_`#>~]")
_WS_RE = re.compile(r"\s+")


def to_plain_text(text: str) -> str:
    """Replicates PocketPal toPlainText: strip tags, md images, md links->label, emphasis, collapse ws."""
    text = _MD_IMG_RE.sub("", text or "")
    text = _MD_LINK_RE.sub(r"\1", text)
    text = _TAG_RE.sub("", text)
    text = _EMPH_RE.sub("", text)
    return _WS_RE.sub(" ", text).strip()


def truncate_on_word_boundary(text: str, max_chars: int) -> str:
    """Replicates PocketPal truncateOnWordBoundary: word-boundary cut, append ellipsis."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_space = cut.rfind(" ")
    if last_space > max_chars // 2:  # word boundary if reasonable, else hard char cut
        cut = cut[:last_space]
    return cut.rstrip() + "…"


def read_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def append_jsonl(path, obj):
    with open(path, "a") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
