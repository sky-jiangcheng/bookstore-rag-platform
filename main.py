"""Unified production entrypoint for the consolidated BookStore platform."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
GATEWAY_DIR = REPO_ROOT / "apps" / "bookstore-gateway"
GATEWAY_SHARED_DIR = GATEWAY_DIR / "shared"

for path in (GATEWAY_SHARED_DIR, GATEWAY_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from bookstore_shared import create_service_app


app = create_service_app("platform")
