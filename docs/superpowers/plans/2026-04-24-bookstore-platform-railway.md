# BookStore Platform Railway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the consolidated BookStore platform as one Railway service that serves the frontend and backend from the same origin.

**Architecture:** The repository keeps modular internal code, but production runs through a single `main.py` entrypoint and a single root `Dockerfile`. The backend exposes only the core auth and recommendation/booklist flows, while the built frontend is copied into the image and mounted as static assets at `/`. Railway owns the one public service, the database, and the cache/vector resources.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, Railway, Vite, Vue 3, PostgreSQL, Redis, Qdrant, npm.

---

### Task 1: Lock the single-service runtime contract

**Files:**
- Modify: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/main.py`
- Modify: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/apps/bookstore-gateway/shared/bookstore_shared/service_factory.py`
- Test: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/main.py` import smoke

- [ ] **Step 1: Confirm the platform app boots only the core routes**

Run:
```bash
python3 -c "import sys; from pathlib import Path; repo=Path('/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform'); sys.path.insert(0, str(repo/'apps'/'bookstore-gateway'/'shared')); sys.path.insert(0, str(repo/'apps'/'bookstore-gateway')); sys.path.insert(0, str(repo)); import main; print(main.app.title)"
```
Expected: prints `书店智能管理系统API (platform)`.

- [ ] **Step 2: Confirm the exposed route set is only the core flows**

Run:
```bash
python3 -c "import sys; from pathlib import Path; repo=Path('/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform'); sys.path.insert(0, str(repo/'apps'/'bookstore-gateway'/'shared')); sys.path.insert(0, str(repo/'apps'/'bookstore-gateway')); sys.path.insert(0, str(repo)); import main; paths=sorted({getattr(r,'path',None) for r in main.app.routes if getattr(r,'path',None)}); print('\\n'.join(p for p in paths if p.startswith('/api') or p in ['/', '/health']))"
```
Expected: routes for `/api/v1/auth/*`, `/api/v1/smart/*`, `/api/v1/book-list/*`, `/api/v1/recommendation/*`, `/api/v1/demand-analysis/*`, `/api/v1/booklist/*`, `/api/v1/agent/*`, `/health`, and `/`.

- [ ] **Step 3: Keep static asset mounting compatible with Railway**

Update `service_factory.py` so the `platform` app serves frontend assets from `apps/bookstore-frontend/dist` when present, and falls back to a JSON root response when the assets are absent.

---

### Task 2: Make the production image build the frontend and backend together

**Files:**
- Add: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/Dockerfile`
- Modify: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/apps/bookstore-frontend/package.json` only if the production build needs a new script
- Test: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/apps/bookstore-frontend` build

- [ ] **Step 1: Build the frontend inside the image**

Use the existing Vite build so the image copies `apps/bookstore-frontend/dist` into the backend stage.

- [ ] **Step 2: Ensure the backend stage has the right Python path**

Keep `PYTHONPATH` pointed at `/app` and `apps/bookstore-gateway/shared` so `main.py` can import the shared app factory.

- [ ] **Step 3: Verify the Dockerfile starts the platform app**

Run:
```bash
python3 -m py_compile /Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/main.py /Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/apps/bookstore-gateway/shared/bookstore_shared/service_factory.py
```
Expected: no syntax errors.

---

### Task 3: Replace the old multi-service Railway layout with one service

**Files:**
- Modify: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/railway.toml`
- Modify: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/DEPLOYMENT_README.md`
- Modify: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/README.md`
- Modify: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/DEPLOYMENT_SUMMARY.md`
- Modify: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/RAILWAY_DEPLOYMENT.md`

- [ ] **Step 1: Point Railway at the root Dockerfile**

Keep only one web service named `platform` in the Railway config.

- [ ] **Step 2: Remove the old Gateway/Auth/Catalog/Ops deployment instructions**

Rewrite the docs so they describe one deployment target, one domain, and one set of environment variables.

- [ ] **Step 3: Align the README with the production shape**

State clearly that the repository now produces a single platform service and that the old modules are historical/internal.

---

### Task 4: Verify the core user flow end to end

**Files:**
- Test: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/main.py`
- Test: `/Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/apps/bookstore-frontend`

- [ ] **Step 1: Rebuild the frontend**

Run:
```bash
cd /Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform/apps/bookstore-frontend && npm run build
```
Expected: build succeeds and emits `dist/`.

- [ ] **Step 2: Smoke the platform app import and route table again**

Run the two `python3 -c ...` checks from Task 1.

- [ ] **Step 3: Validate that the core APIs still exist**

Check that login and recommendation routes are still mounted before any Railway deploy attempt.

---

### Task 5: Deploy and confirm on Railway

**Files:**
- No code changes unless Railway reveals an environment mismatch

- [ ] **Step 1: Deploy the root service to Railway**

Run:
```bash
cd /Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform && railway up
```
Expected: build completes and a single service URL is produced.

- [ ] **Step 2: Confirm production health**

Run:
```bash
curl -f https://<railway-domain>/health
```
Expected: `200` with healthy payload.

- [ ] **Step 3: Smoke the user journey**

Verify login, recommendation, booklist generation, and export from the Railway domain.

---

### Self-Review Notes

- The plan keeps to one production service and does not reintroduce catalog/ops as deploy targets.
- The only public runtime surface is the consolidated platform.
- The validation steps are concrete and use the exact files and commands that exist in the repository.
