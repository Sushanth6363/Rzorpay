"""Load `.env` into the process environment — stdlib only, no new dependency.

WHY THIS EXISTS
    Every credential in this project is read with `os.environ.get(...)`, so a populated
    `.env` file was pure documentation until something loaded it. The failure mode was
    quiet and expensive: the engine reports NOT_CONFIGURED, refuses to send, and the
    person running it concludes the integration is broken when the file was simply never
    read. On a demo day that is the worst possible place to lose ten minutes.

INVARIANTS:
1. NEVER OVERRIDES A REAL ENVIRONMENT VARIABLE. Anything already exported wins, so CI,
   containers and `RECOVERY_DISPATCH_ENABLED=false pytest` behave as the caller intended
   and a stale `.env` on a developer's disk cannot silently change what a test does.
2. NEVER LOGS A VALUE. Only the count of keys loaded and their NAMES, never contents.
3. SILENT WHEN ABSENT. No `.env` is the normal state for the offline batch path.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse KEY=VALUE lines. Tolerates comments, blanks, `export `, and quoted values."""
    values: Dict[str, str] = {}
    if not path.exists():
        return values

    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        # Strip one matching pair of surrounding quotes; a Gmail app password or a
        # base64 secret can legitimately contain characters that look like syntax.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def load_dotenv(path: Path = ENV_PATH, override: bool = False) -> List[str]:
    """Load `.env` into os.environ. Returns the NAMES of keys applied, never values."""
    applied: List[str] = []
    for key, value in parse_env_file(path).items():
        if not override and key in os.environ:
            continue
        os.environ[key] = value
        applied.append(key)
    return applied


# Loaded on import so any entrypoint - webhook server, dashboard, CLI - picks it up
# without each having to remember to call it.
LOADED_KEYS = load_dotenv()
