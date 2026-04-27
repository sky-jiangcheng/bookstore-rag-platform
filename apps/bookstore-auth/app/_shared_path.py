"""Ensure the shared backend package is importable."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_shared_backend_path() -> None:
    # auth/app/_shared_path.py -> parents[1] = repo_root
    repo_root = Path(__file__).resolve().parents[1]
    shared_backend = repo_root / "shared"

    path_str = str(shared_backend)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
