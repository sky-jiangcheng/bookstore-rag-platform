API Contract & Integration Guide

Overview
- local-platform (frontend) will call agentic-rag hosted API to parse user input and generate book-lists.
- Set VITE_API_BASE_URL to full origin (e.g., https://bookstore.example.com/api/v1)

Endpoints (examples)
1) Parse requirements
   POST {BASE}/book-list/parse
   Headers: Authorization: Bearer <JWT>
   Body: {"user_input": "推荐10本适合大学新生的编程入门书", "use_history": true}
   Example Response (200):
   {
     "request_id": "uuid-...",
     "parsed_requirements": { "keywords": ["编程","入门"], "categories": [] },
     "confidence_score": 0.92,
     "needs_confirmation": false,
     "message": "需求解析完成"
   }

2) Generate book list (sync)
   POST {BASE}/book-list/generate
   Headers: Authorization: Bearer <JWT>
   Body: {"request_id": "uuid-...", "limit": 12}
   Example Response (200):
   {
     "request_id": "uuid-...",
     "recommendations": [ {"book_id":"b1","title":"...","price":45.0} ],
     "total_count": 12,
     "category_distribution": {"计算机": 8},
     "generation_time_ms": 850
   }

3) Async alternative
   - If response is 202, server returns {"job_id":"..."} and pushes result to configured callback URL or client polls GET /book-list/{job_id}

4) Health
   GET {BASE}/health -> {"status":"ok"}

Integration checklist
- Frontend: ensure VITE_API_BASE_URL points to the origin including /api/v1 suffix. For local orchestration set it to the gateway (e.g. http://localhost:8000/api/v1).
- Auth: obtain JWT from auth service; set Authorization header.
- CORS: agentic-rag must allow origin of the gateway and/or the gateway proxies calls (gateway will forward requests server-side so CORS is less strict for frontend).
- Export: frontend will render and call exportBookListToExcel for user-download.

Testing steps (local)
1) Set .env.local VITE_API_BASE_URL=http://localhost:8000/api/v1
2) Start bookstore-gateway (uvicorn app.main:app --reload --port 8000) and any required services
3) Start local-platform front-end
4) Use UI to run parse->generate flow; gateway will forward to the remote agentic-rag (configured via AGENTIC_BASE_URL env var) and return results
5) Verify frontend shows recommendations and Export button downloads .xls

If you want, next steps I can:
- Generate client stubs from the OpenAPI spec (TS/JS)
- Add example JWT generation (dev-only) and a tiny mock server for local testing
- Patch frontend to add a small integration test harness

