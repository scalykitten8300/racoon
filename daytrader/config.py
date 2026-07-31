"""Shared configuration for where account/portfolio data is stored."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def default_data_dir() -> Path:
    """Root directory for persisted user/portfolio data.

    Honors DAYTRADER_DATA_DIR so tests (and callers) can redirect
    storage without touching the real on-disk data.
    """
    env_dir = os.environ.get("DAYTRADER_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return REPO_ROOT / "daytrader_data"
