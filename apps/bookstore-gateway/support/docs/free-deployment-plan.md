# 免费部署方案

目标：

- 前端部署到 Cloudflare Pages
- 后端部署到 Fly.io
- 保留智能推荐主线，不牺牲书单生成、模板、反馈和 Agent 入口

## 前端

- 构建命令：`npm run build`
- 输出目录：`dist`
- 需要配置的环境变量：
  - `VITE_API_BASE_URL=https://<fly-app>.fly.dev/api/v1`
- 开发态保持 `vite` 代理不变，生产态由环境变量指向 Fly 后端

## 后端

- 启动方式：`cd backend/services/gateway && uvicorn main:app`
- 推荐环境变量：
  - `APP_ENV=free_cloud`（优先使用线上免费资源）
  - `JWT_SECRET_KEY`
  - `ADMIN_PASSWORD`
  - `OPENAI_API_KEY`、`GEMINI_API_KEY`、`QWEN_API_KEY`、`ERNIE_API_KEY`
  - `CORS_ORIGINS=https://<pages-domain>`
- 数据存储：
  - 线上免费资源优先：`DATABASE_URL` 指向免费数据库
  - 不想接外部库时可退回 Fly volume 上的 SQLite
- 向量检索：
  - 优先使用 `QDRANT_URL` + `QDRANT_API_KEY` 接 Qdrant Cloud Free
  - 失败时自动回退本地向量库
  - 会从 `BookInfo.embedding` 回填本地向量库，减少重启后的推荐失忆
- 任务队列：
  - 优先使用 `UPSTASH_REDIS_URL`
  - 没有 Redis 时继续用 `AsyncTaskManager`

## 需要保留的能力

- 智能推荐
- 书单生成
- 模板加载与分享
- Agent 书单助手
- 反馈与历史记录

## 说明

- 这个方案的目标是“先免费上线，再逐步增强”
- 上线前请优先查看 [free-cloud-checklist.md](/Users/jiangcheng/Workspace/Python/BookStore/docs/free-cloud-checklist.md)
- 一页式执行版见 [free-cloud-one-pager.md](/Users/jiangcheng/Workspace/Python/BookStore/docs/free-cloud-one-pager.md)
- 如果后续要恢复更强的持久化和检索能力，可以再把 SQLite / 本地向量切换回托管数据库与 Qdrant
- 前端通过 `VITE_API_BASE_URL` 直连 Fly 后端，避免和 Cloudflare Pages 同源绑定
- 免费资源优先级建议：
  - 数据库：Supabase / Neon / PlanetScale 任选其一，通过 `DATABASE_URL` 接入
  - 向量库：Qdrant Cloud Free
  - 缓存/短期队列：Upstash Redis Free
