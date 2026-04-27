# Free Cloud Checklist

## Must set

- [ ] `APP_ENV=free_cloud`
- [ ] `VITE_API_BASE_URL=https://<your-fly-app>.fly.dev/api/v1`
- [ ] `CORS_ORIGINS=https://<your-pages-domain>`
- [ ] `DATABASE_URL` or Fly volume-backed SQLite
- [ ] `QDRANT_URL` and `QDRANT_API_KEY`
- [ ] `UPSTASH_REDIS_URL`
- [ ] `JWT_SECRET_KEY`
- [ ] `ADMIN_PASSWORD`
- [ ] At least one LLM key, for example `GEMINI_API_KEY`

## Recommended

- [ ] Mount Fly volume at `/data`
- [ ] Use a free SQL provider for stronger durability
- [ ] Use Qdrant Cloud Free to keep semantic recommendation quality
- [ ] Use Upstash Redis Free for cache/short tasks

## Deploy order

1. Create external resources.
2. Set Fly secrets and mount `/data`.
3. Deploy backend.
4. Deploy Cloudflare Pages.
5. Verify login, import, recommendation, share, and agent chat.

## Fail fast

- Missing `CORS_ORIGINS` should stop backend startup.
- Missing `VITE_API_BASE_URL` should block production deployment.
- Missing embeddings will reduce recommendation quality until import/backfill finishes.
