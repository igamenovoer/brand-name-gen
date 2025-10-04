"""
Environment helpers (.env precedence).

Provides small utilities to load a local `.env` into the environment and
to read a specific key from `.env` without mutating `os.environ`.
"""

from __future__ import annotations

import os
from typing import Optional


def load_env_from_dotenv() -> None:
    """Load KEY=VALUE pairs from `.env` in CWD into os.environ (no override).

    - Ignores blank lines and comments starting with '#'
    - Strips surrounding single/double quotes from values
    - Does not overwrite existing environment variables
    """

    path = os.path.join(os.getcwd(), ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                key = k.strip()
                val = v.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:  # pragma: no cover - defensive
        return


def read_dotenv_value(key: str) -> Optional[str]:
    """Return value for `key` from `.env` in CWD, without modifying env.

    Returns None if `.env` not present or key not found.
    """

    path = os.path.join(os.getcwd(), ".env")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    except Exception:  # pragma: no cover - defensive
        return None
    return None

