# BookStore Local Platform - Single Service Deploy

> 生产部署只保留一个 Railway `platform` 服务，由根目录 `Dockerfile` 构建前后端一体镜像，入口是 `main.py`。

## 项目结构

```text
bookstore-local-platform/
├── Dockerfile
├── railway.toml
├── main.py
└── apps/
    ├── bookstore-gateway/    # 平台共享后端代码
    ├── bookstore-auth/       # 历史认证模块，保留为内部代码
    ├── bookstore-rag/        # 历史推荐模块，保留为内部代码
    └── bookstore-frontend/   # 前端页面
```

## 部署目标

- 一个 Railway 服务：`platform`
- 一个对外域名
- 前端静态资源和后端 API 同域
- 仓库内模块保留，但不再作为独立 Railway 服务部署

## 必要环境变量

- `APP_ENV=free_cloud`
- `CORS_ORIGINS=https://<railway-domain>`
- `DATABASE_URL`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `UPSTASH_REDIS_URL`
- `JWT_SECRET_KEY`
- `ADMIN_PASSWORD`
- 至少一个模型密钥，例如 `GEMINI_API_KEY`

## 部署步骤

1. 创建 Railway 项目并连接仓库根目录。
2. 在项目里添加数据库、Redis、Qdrant 资源。
3. 配置上面的环境变量。
4. 执行 `railway up`，让根目录 `Dockerfile` 构建前端并启动 `main.py`。
5. 打开部署后的域名，确认 `/health`、登录、推荐和导出都正常。

## 验证清单

- `GET /health` 返回正常
- 登录接口返回 token
- 推荐接口能返回书单
- 书单导出能下载 Excel

## 备注

- Railway 只保留单服务平台，不再使用旧的多服务部署说明。
- `apps/` 下的模块是仓库内部实现细节，不是独立生产入口。
