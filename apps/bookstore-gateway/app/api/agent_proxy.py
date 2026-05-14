"""
Agent Proxy - Orchestrates calls from local-platform to agentic-rag backend.
Forwards parse/generate requests, injects/forwards auth, adds retries and error mapping.
"""
from typing import Optional
import os
import asyncio
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
import httpx

from app.api.auth_management import get_current_active_user
from app.api.v1.book_list import schemas as booklist_schemas

logger = logging.getLogger(__name__)
router = APIRouter()

AGENTIC_BASE = os.getenv("AGENTIC_BASE_URL", "https://bookstore-agentic-rag.vercel.app")
SERVICE_TOKEN = os.getenv("AGENTIC_SERVICE_TOKEN")  # optional service JWT for server-to-server calls

# Shared AsyncClient to reuse connections and limits
DEFAULT_TIMEOUT = httpx.Timeout(25.0)
DEFAULT_LIMITS = httpx.Limits(max_keepalive_connections=10, max_connections=50)
_client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, limits=DEFAULT_LIMITS)


async def _close_client() -> None:
    try:
        await _client.aclose()
    except Exception as e:
        logger.warning("Error closing httpx client: %s", e)


async def forward_request(path: str, json_body: dict, auth_header: Optional[str] = None):
    url = AGENTIC_BASE.rstrip("/") + path
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Prefer explicit Authorization header passed from upstream request
    if auth_header:
        headers["Authorization"] = auth_header
    elif SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {SERVICE_TOKEN}"

    retries = 2
    backoff_base = 0.3

    for attempt in range(retries + 1):
        try:
            resp = await _client.post(url, json=json_body, headers=headers)
            if resp.status_code >= 500 and attempt < retries:
                sleep_s = backoff_base * (2 ** attempt)
                logger.info("Transient error from agentic (%s), retrying after %.2fs", resp.status_code, sleep_s)
                await asyncio.sleep(sleep_s)
                continue
            return resp
        except httpx.RequestError as exc:
            if attempt < retries:
                sleep_s = backoff_base * (2 ** attempt)
                logger.info("httpx request error, retrying after %.2fs: %s", sleep_s, exc)
                await asyncio.sleep(sleep_s)
                continue
            logger.error("Request to agentic failed: %s", exc)
            raise


def _parse_response_content(resp: httpx.Response):
    try:
        return resp.json()
    except Exception:
        # fallback to text
        return {"detail": resp.text}


@router.post("/parse", response_model=booklist_schemas.ParseRequirementsResponse)
async def proxy_parse(
    request: Request,
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
):
    """Proxy parse request to agentic-rag. Forwards Authorization header if present, else uses service token."""
    auth_header = request.headers.get("Authorization")

    try:
        resp = await forward_request("/api/v1/book-list/parse", body, auth_header)
    except Exception as e:
        logger.exception("Failed to forward parse request")
        raise HTTPException(status_code=502, detail="Forwarding to agentic service failed")

    if resp.status_code >= 400:
        content = _parse_response_content(resp)
        # Surface agent error details where safe
        raise HTTPException(status_code=resp.status_code, detail=content)

    return _parse_response_content(resp)


@router.post("/generate", response_model=booklist_schemas.GenerateBookListResponse)
async def proxy_generate(
    request: Request,
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
):
    """Proxy generate request to agentic-rag. Forwards Authorization header if present, else uses service token."""
    auth_header = request.headers.get("Authorization")

    try:
        resp = await forward_request("/api/v1/book-list/generate", body, auth_header)
    except Exception as e:
        logger.exception("Failed to forward generate request")
        raise HTTPException(status_code=502, detail="Forwarding to agentic service failed")

    if resp.status_code >= 400:
        content = _parse_response_content(resp)
        raise HTTPException(status_code=resp.status_code, detail=content)

    return _parse_response_content(resp)


from fastapi.responses import StreamingResponse


@router.post('/export')
async def proxy_export(
    request: Request,
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
):
    """Proxy export request and stream binary response (e.g., Excel file) back to client."""
    auth_header = request.headers.get("Authorization")
    url = AGENTIC_BASE.rstrip("/") + "/api/v1/book-list/export-excel"
    headers = {"Accept": "*/*", "Content-Type": "application/json"}
    if auth_header:
        headers["Authorization"] = auth_header
    elif SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {SERVICE_TOKEN}"

    try:
        stream = await _client.stream("POST", url, json=body, headers=headers)
    except Exception:
        logger.exception("Failed to stream export from agentic")
        raise HTTPException(status_code=502, detail="Export forwarding failed")

    if stream.status_code >= 400:
        content = _parse_response_content(await stream.aread()) if hasattr(stream, 'aread') else {"detail": "export failed"}
        raise HTTPException(status_code=stream.status_code, detail=content)

    # Build StreamingResponse to client
    resp_headers = stream.headers
    content_type = resp_headers.get('content-type', 'application/octet-stream')
    disposition = resp_headers.get('content-disposition')

    async def iter_bytes():
        async for chunk in stream.aiter_bytes():
            yield chunk
        await stream.aclose()

    streaming_response = StreamingResponse(iter_bytes(), media_type=content_type)
    if disposition:
        streaming_response.headers['Content-Disposition'] = disposition
    return streaming_response


# Optional: provide a graceful shutdown hook if the application uses it
try:
    # FastAPI will prefer app-level lifespan to close clients; keep safe fallback
    import atexit

    atexit.register(lambda: asyncio.get_event_loop().run_until_complete(_close_client()))
except Exception:
    pass
