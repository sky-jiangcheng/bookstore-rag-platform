# Free Cloud Deploy Steps

Use this with [free-cloud-checklist.md](/Users/jiangcheng/Workspace/Python/BookStore/docs/free-cloud-checklist.md).

## 1. Prepare resources

1. Create or choose a database target.
   - Preferred: free SQL provider via `DATABASE_URL`
   - Fallback: Fly volume-backed SQLite at `/data/bookstore.db`
2. Create a Qdrant Cloud Free cluster and copy `QDRANT_URL` and `QDRANT_API_KEY`.
3. Create an Upstash Redis Free instance and copy `UPSTASH_REDIS_URL`.
4. Prepare at least one LLM key, such as `GEMINI_API_KEY` or `OPENAI_API_KEY`.

## 2. Configure Fly backend

1. Set `APP_ENV=free_cloud`.
2. Set secrets:
   - `DATABASE_URL`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
   - `UPSTASH_REDIS_URL`
   - `JWT_SECRET_KEY`
   - `ADMIN_PASSWORD`
   - `CORS_ORIGINS`
   - LLM API keys
3. Mount the Fly volume at `/data`.
4. Deploy the backend container from `fly.toml`.
5. Verify `GET /health` returns `{"status":"healthy"}`.

## 3. Configure Cloudflare Pages

1. Build command: `npm run build`
2. Output directory: `dist`
3. Set `VITE_API_BASE_URL=https://<your-fly-app>.fly.dev/api/v1`
4. Keep `frontend/public/_redirects`.
5. Make sure the Pages domain matches backend `CORS_ORIGINS`.

## 4. Verify core flows

- Login
- Import
- Smart recommendation
- Book list generation
- Template share link
- Agent chat

## 5. Fallback rules

- Qdrant Cloud unavailable -> local vector fallback
- Redis unavailable -> in-memory task/cache fallback
- No embeddings yet -> recommendation quality is limited until import/backfill completes
