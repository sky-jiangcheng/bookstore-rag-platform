"""Shared RAG backend selector.

This module lets every service reuse the same book recommendation capability
while choosing between a local in-process implementation and a remote
agentic-RAG service deployed elsewhere.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

import httpx

logger = logging.getLogger(__name__)


class RAGBackend(Protocol):
    """Minimal interface used by the recommendation endpoints."""

    async def get_book_recommendations(
        self,
        user_input: str,
        db: Any = None,
        limit: int = 20,
        authorization: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return recommendation payload."""


@dataclass
class RemoteRAGService:
    """Async HTTP client for a dedicated rag service."""

    base_url: str
    timeout_seconds: float = 30.0

    async def get_book_recommendations(
        self,
        user_input: str,
        db: Any = None,
        limit: int = 20,
        authorization: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"user_input": user_input, "limit": limit}
        headers = {"Content-Type": "application/json"}
        if authorization:
            headers["Authorization"] = authorization

        url = f"{self.base_url}/smart/recommendation"

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=20),
        ) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.RequestError as exc:
                raise RuntimeError(f"Remote RAG service unreachable: {exc}") from exc

        if resp.status_code >= 400:
            logger.error(
                "Remote RAG request failed with HTTP %s: %s",
                resp.status_code,
                resp.text[:500],
            )
            raise RuntimeError(
                f"Remote RAG service returned HTTP {resp.status_code}: {resp.text[:500]}"
            )

        try:
            return resp.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Remote RAG service returned invalid JSON: {resp.text[:500]}"
            ) from exc


@dataclass
class LocalRAGService:
    """In-process adapter around the local RAGService implementation."""

    service: Any

    async def get_book_recommendations(
        self,
        user_input: str,
        db: Any = None,
        limit: int = 20,
        authorization: Optional[str] = None,
    ) -> Dict[str, Any]:
        del authorization
        return self.service.get_book_recommendations(
            user_input=user_input,
            db=db,
            limit=limit,
        )


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def build_rag_backend(
    vector_db: Any = None,
    gemini_service: Any = None,
    llm_service: Any = None,
) -> RAGBackend:
    """Create a reusable RAG backend for the current runtime.

    If ``RAG_SERVICE_URL`` is configured, the backend delegates to the
    dedicated service over HTTP. Otherwise it falls back to the local
    in-process ``RAGService`` implementation.
    """

    remote_url = os.getenv("RAG_SERVICE_URL", "").strip()
    if remote_url:
        return RemoteRAGService(base_url=_normalize_base_url(remote_url))

    from app.services.gemini_service import GeminiService
    from app.services.llm_service import LLMService
    from app.services.rag_service import RAGService
    from app.services.vector_db_service import vector_db as default_vector_db

    resolved_vector_db = vector_db if vector_db is not None else default_vector_db
    resolved_gemini_service = gemini_service or GeminiService()
    resolved_llm_service = llm_service or LLMService()

    return LocalRAGService(
        service=RAGService(
            vector_db=resolved_vector_db,
            gemini_service=resolved_gemini_service,
            llm_service=resolved_llm_service,
        )
    )
