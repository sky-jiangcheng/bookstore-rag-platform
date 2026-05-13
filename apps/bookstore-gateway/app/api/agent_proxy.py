"""
Agent Proxy - Orchestrates calls from local-platform to agentic-rag backend.
Forwards parse/generate requests, injects/forwards auth, adds retries and error mapping.
"""
from typing import Optional
import os
import asyncio

from fastapi import APIRouter, Body, Depends, HTTPException
import httpx

from app.api.auth_management import get_current_active_user
from app.api.v1.book_list import schemas as booklist_schemas

router = APIRouter()

AGENTIC_BASE = os.getenv("AGENTIC_BASE_URL", "https://bookstore-agentic-rag.vercel.app")
SERVICE_TOKEN = os.getenv("AGENTIC_SERVICE_TOKEN")  # optional service JWT for server-to-server calls

DEFAULT_TIMEOUT = 25.0

async def forward_request(path: str, json_body: dict, token: Optional[str] = None):
    url = AGENTIC_BASE.rstrip("/") + path
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {SERVICE_TOKEN}"

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        # simple retry loop for transient errors
        retries = 2
        for attempt in range(retries + 1):
            try:
                resp = await client.post(url, json=json_body, headers=headers)
                # directly raise for 4xx/5xx to capture body
                if resp.status_code >= 500 and attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                return resp
            except httpx.RequestError as exc:
                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise


@router.post("/parse", response_model=booklist_schemas.ParseRequirementsResponse)
async def proxy_parse(
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
):
    """Proxy parse request to agentic-rag with user token or service token."""
    token = None
    try:
        token = getattr(current_user, "access_token", None) or None
    except Exception:
        token = None

    try:
        resp = await forward_request("/api/v1/book-list/parse", body, token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Forwarding failed: {e}")

    if resp.status_code >= 400:
        # bubble up error
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


@router.post("/generate", response_model=booklist_schemas.GenerateBookListResponse)
async def proxy_generate(
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
):
    """Proxy generate request to agentic-rag with user token or service token."""
    token = None
    try:
        token = getattr(current_user, "access_token", None) or None
    except Exception:
        token = None

    try:
        resp = await forward_request("/api/v1/book-list/generate", body, token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Forwarding failed: {e}")

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()
