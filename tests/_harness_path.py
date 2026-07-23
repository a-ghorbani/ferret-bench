"""Import shim so tests run from anywhere until the package layout lands.

The harness modules use `sys.path.insert` and are imported as top-level names
(`import common`), so tests must put harness/ on the path before importing them.
When harness/ becomes a real package this file collapses to a normal import.
"""
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent / "harness"
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

import agent_loop  # noqa: E402,F401
import common  # noqa: E402,F401
import configs  # noqa: E402,F401
import http_cache  # noqa: E402,F401

__all__ = ["common", "configs", "http_cache", "agent_loop", "HARNESS_DIR"]
