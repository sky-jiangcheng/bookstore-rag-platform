"""Backward-compatible wrapper around shared backend service factory."""

from app._shared_path import ensure_shared_backend_path

ensure_shared_backend_path()

from bookstore_shared.service_factory import SERVICE_ROUTES, RouterSpec, create_service_app

__all__ = ["SERVICE_ROUTES", "RouterSpec", "create_service_app"]
