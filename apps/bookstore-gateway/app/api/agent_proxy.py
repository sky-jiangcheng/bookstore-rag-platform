"""
Agent Proxy - Orchestrates calls from local-platform to agentic-rag backend.
Forwards parse/generate/export requests, injects/forwards auth, adds retries,
error mapping, X-Request-ID propagation, and Prometheus metrics.

The shared httpx.AsyncClient is created/closed via FastAPI lifespan in
service_factory.create_service_app() and stored on app.state.agentic_client.
"""
import asyncio
import logging
import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
import httpx

from app.api.auth_management import get_current_active_user
from app.api.v1.book_list import schemas as booklist_schemas
from app.core.metrics import MetricsCollector

logger = logging.getLogger(__name__)
router = APIRouter()

AGENTIC_BASE = os.environ.get("AGENTIC_BASE_URL", "https://bookstore-agentic-rag.vercel.app")
SERVICE_TOKEN = os.environ.get("AGENTIC_SERVICE_TOKEN")


def _get_client(request: Request) -> httpx.AsyncClient:
    """Return the lifespan-managed httpx client from app state."""
    client = getattr(request.app.state, "agentic_client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Agentic proxy client not initialized")
    return client


def _build_headers(request: Request, auth_header: Optional[str] = None) -> dict:
    """Build upstream headers with auth and tracing propagation."""
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    if auth_header:
        headers["Authorization"] = auth_header
    elif SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {SERVICE_TOKEN}"

    # Propagate or generate X-Request-ID for distributed tracing
    request_id = request.headers.get("X-Request-ID") or getattr(
        request.state, "request_id", None
    ) or str(uuid.uuid4())
    headers["X-Request-ID"] = request_id

    # Forward traceparent if present (W3C Trace Context)
    traceparent = request.headers.get("traceparent")
    if traceparent:
        headers["traceparent"] = traceparent

    return headers


async def forward_request(
    client: httpx.AsyncClient,
    path: str,
    json_body: dict,
    headers: dict,
    endpoint_label: str = "agent",
):
    """Forward a request with retry/backoff and metrics."""
    url = AGENTIC_BASE.rstrip("/") + path
    retries = 2
    backoff_base = 0.3
    start = time.time()

    for attempt in range(retries + 1):
        try:
            resp = await client.post(url, json=json_body, headers=headers)
            if resp.status_code >= 500 and attempt < retries:
                sleep_s = backoff_base * (2 ** attempt)
                MetricsCollector.record_proxy_retry(endpoint_label, f"status_{resp.status_code}")
                logger.info(
                    "Transient error %d from agentic (%s), retry %.2fs",
                    resp.status_code, path, sleep_s,
                )
                await asyncio.sleep(sleep_s)
                continue
            return resp
        except httpx.RequestError as exc:
            if attempt < retries:
                sleep_s = backoff_base * (2 ** attempt)
                MetricsCollector.record_proxy_retry(endpoint_label, type(exc).__name__)
                logger.info("httpx error, retry %.2fs: %s", sleep_s, exc)
                await asyncio.sleep(sleep_s)
                continue
            duration = time.time() - start
            MetricsCollector.record_error("upstream_unavailable", endpoint_label)
            MetricsCollector.record_proxy_forward(endpoint_label, 502, duration)
            logger.error("Request to agentic failed after %d attempts (%.2fs): %s", retries + 1, duration, exc)
            raise

    # Should not reach here, but satisfy type checkers
    raise httpx.RequestError("Exhausted retries")


def _parse_response_content(resp: httpx.Response):
    try:
        return resp.json()
    except Exception:
        return {"detail": resp.text}


@router.post("/parse", response_model=booklist_schemas.ParseRequirementsResponse)
async def proxy_parse(
    request: Request,
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
):
    """Proxy parse request to agentic-rag."""
    client = _get_client(request)
    headers = _build_headers(request, request.headers.get("Authorization"))
    start = time.time()

    try:
        resp = await forward_request(client, "/api/v1/book-list/parse", body, headers, "agent_parse")
    except Exception:
        logger.exception("Failed to forward parse request")
        raise HTTPException(status_code=502, detail="Forwarding to agentic service failed")

    duration = time.time() - start
    MetricsCollector.record_proxy_forward("agent_parse", resp.status_code, duration)

    if resp.status_code >= 400:
        content = _parse_response_content(resp)
        raise HTTPException(status_code=resp.status_code, detail=content)

    return _parse_response_content(resp)


@router.post("/generate", response_model=booklist_schemas.GenerateBookListResponse)
async def proxy_generate(
    request: Request,
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
):
    """Proxy generate request to agentic-rag."""
    client = _get_client(request)
    headers = _build_headers(request, request.headers.get("Authorization"))
    start = time.time()

    try:
        resp = await forward_request(client, "/api/v1/book-list/generate", body, headers, "agent_generate")
    except Exception:
        logger.exception("Failed to forward generate request")
        raise HTTPException(status_code=502, detail="Forwarding to agentic service failed")

    duration = time.time() - start
    MetricsCollector.record_proxy_forward("agent_generate", resp.status_code, duration)

    if resp.status_code >= 400:
        content = _parse_response_content(resp)
        raise HTTPException(status_code=resp.status_code, detail=content)

    return _parse_response_content(resp)


@router.post("/export")
async def proxy_export(
    request: Request,
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
):
    """Proxy export request and stream binary response (e.g., Excel) back to client."""
    client = _get_client(request)
    auth_header = request.headers.get("Authorization")
    url = AGENTIC_BASE.rstrip("/") + "/api/v1/book-list/export-excel"
    headers = {"Accept": "*/*", "Content-Type": "application/json"}

    if auth_header:
        headers["Authorization"] = auth_header
    elif SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {SERVICE_TOKEN}"

    # Propagate tracing headers
    request_id = request.headers.get("X-Request-ID") or getattr(
        request.state, "request_id", None
    ) or str(uuid.uuid4())
    headers["X-Request-ID"] = request_id
    traceparent = request.headers.get("traceparent")
    if traceparent:
        headers["traceparent"] = traceparent

    start = time.time()

    try:
        stream = await client.stream("POST", url, json=body, headers=headers)
    except Exception:
        MetricsCollector.record_error("upstream_unavailable", "agent_export")
        logger.exception("Failed to stream export from agentic")
        raise HTTPException(status_code=502, detail="Export forwarding failed")

    if stream.status_code >= 400:
        content = _parse_response_content(await stream.aread())
        duration = time.time() - start
        MetricsCollector.record_proxy_forward("agent_export", stream.status_code, duration)
        raise HTTPException(status_code=stream.status_code, detail=content)

    content_type = stream.headers.get("content-type", "application/octet-stream")
    disposition = stream.headers.get("content-disposition")

    async def iter_bytes():
        async for chunk in stream.aiter_bytes():
            yield chunk
        await stream.aclose()

    response = StreamingResponse(iter_bytes(), media_type=content_type)
    if disposition:
        response.headers["Content-Disposition"] = disposition
    response.headers["X-Request-ID"] = request_id

    # Record metrics after streaming completes (approximate)
    duration = time.time() - start
    MetricsCollector.record_proxy_forward("agent_export", stream.status_code, duration)

    return response
