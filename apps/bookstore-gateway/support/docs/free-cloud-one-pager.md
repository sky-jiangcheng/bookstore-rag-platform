# Free Cloud One-Pager

## Stack

- Frontend: Cloudflare Pages
- Backend: Fly.io
- Vector DB: Qdrant Cloud Free
- Cache/queue: Upstash Redis Free
- Database: free SQL provider, or Fly volume-backed SQLite fallback

## Must set

- `APP_ENV=free_cloud`
- `VITE_API_BASE_URL=https://<your-fly-app>.fly.dev/api/v1`
- `CORS_ORIGINS=https://<your-pages-domain>`
- `DATABASE_URL` or `/data/bookstore.db`
- `QDRANT_URL` and `QDRANT_API_KEY`
- `UPSTASH_REDIS_URL`
- `JWT_SECRET_KEY`
- `ADMIN_PASSWORD`
- One LLM key, for example `GEMINI_API_KEY`

## Deploy

1. Create free SQL, Qdrant, and Upstash resources if you want all cloud-backed services.
2. Set Fly secrets and mount the Fly volume at `/data`.
3. Deploy the backend from `fly.toml`.
4. Deploy Cloudflare Pages with `VITE_API_BASE_URL`.
5. Keep `frontend/public/_redirects`.

## Verify

- `/health`
- Login
- Import
- Smart recommendation
- Book list generation
- Template share
- Agent chat

## Fallbacks

- Qdrant unavailable -> local vector fallback
- Redis unavailable -> in-memory cache/task fallback
- No embeddings yet -> recommendation quality is limited until import/backfill completes
