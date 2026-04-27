"""Backward-compatible wrapper around shared backend bootstrap."""

from app._shared_path import ensure_shared_backend_path

ensure_shared_backend_path()

from bookstore_shared.bootstrap import initialize_runtime, wait_for_database

__all__ = ["initialize_runtime", "wait_for_database"]
