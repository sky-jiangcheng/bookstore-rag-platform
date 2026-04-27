"""RAG service entrypoint."""

from app._shared_path import ensure_shared_backend_path

ensure_shared_backend_path()

from bookstore_shared import create_service_app

app = create_service_app("rag")
