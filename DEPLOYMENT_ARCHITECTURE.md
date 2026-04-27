# 部署架构说明

**最后更新**: 2026-04-27  
**维护者**: Sky Jiangcheng

---

## 概述

本文档规范了 BookStore 两个项目的部署架构，解决了历史配置混乱和隐私泄露的问题。

### 核心原则

- ✅ **单一真实来源**（SSOT）：每个环境只有一套配置
- ✅ **隐私优先**：不在仓库中存储敏感信息
- ✅ **可扩展性**：部署工具可以升级，架构不变
- ✅ **清晰职责**：明确区分生产、过期、保留代码

---

## 当前推荐方案（2026）

### 1. 后端：bookstore-local-platform

#### 1.1 部署目标

| 维度 | 值 |
|------|-----|
| 工具 | Railway（主） / Fly.io（备选） |
| 服务数 | 1（单一 platform 服务） |
| 构建配置 | 根目录 `Dockerfile` |
| 生产入口 | `main.py` → uvicorn |
| 包含内容 | 前端（dist） + 后端（FastAPI） |
| 域名数 | 1（前后端同域） |

#### 1.2 架构图

```
┌──────────────────────────────────────────────────────────┐
│                    Internet                              │
└────────────────────┬─────────────────────────────────────┘
                     │
             HTTPS (Railway Domain)
                     │
        ┌────────────▼─────────────┐
        │    Railway Platform      │
        │  Single Web Service      │
        ├─────────────────────────┤
        │  Frontend (Vue3 dist)   │
        │  served on /             │
        ├─────────────────────────┤
        │  Backend (FastAPI)       │
        │  - /api/v1/*             │
        │  - /health               │
        │  - /docs (Swagger)       │
        ├─────────────────────────┤
        │  Dependencies            │
        │  - PostgreSQL            │
        │  - Redis                 │
        │  - Qdrant                │
        └────────────────────────┘
```

#### 1.3 环境变量

**必需变量**（部署失败则无法启动）：

```env
APP_ENV=free_cloud
JWT_SECRET_KEY=<32-char-hex-random-string>
CORS_ORIGINS=https://<railway-domain>
DATABASE_URL=postgresql://...
QDRANT_URL=http://...
ADMIN_PASSWORD=<strong-password>
GEMINI_API_KEY=<api-key>
```

**可选变量**：

```env
QDRANT_API_KEY=<api-key>  # 如果 Qdrant 启用认证
UPSTASH_REDIS_URL=redis://...  # 如果使用 Upstash
LOG_LEVEL=INFO
```

#### 1.4 部署清单

```bash
# 1. 连接仓库根目录到 Railway
railway login
cd bookstore-local-platform
railway init --name bookstore-platform

# 2. 添加资源
railway add --plugin postgres
railway add --plugin redis
railway add --plugin qdrant

# 3. 设置环境变量
railway variables set APP_ENV="free_cloud"
railway variables set JWT_SECRET_KEY="$(openssl rand -hex 32)"
# ... 其他变量 ...

# 4. 部署
railway up

# 5. 验证
curl -f https://<railway-domain>/health
```

---

### 2. 前端：bookstore-agentic-rag

#### 2.1 部署目标

| 维度 | 值 |
|------|-----|
| 工具 | Vercel |
| 类型 | Next.js 应用 |
| 构建命令 | `npm run build` |
| 生产入口 | Next.js App Router |
| 数据源 | Neon Postgres (DATABASE_URL) |
| 依赖 | Upstash Redis、Upstash Vector |
| 域名 | 独立域名（Vercel 提供） |

#### 2.2 架构图

```
┌──────────────────────────────────────────────────────────┐
│                    Internet                              │
└────────────────────┬─────────────────────────────────────┘
                     │
            HTTPS (Vercel Domain)
                     │
        ┌────────────▼─────────────┐
        │   Vercel Edge Network    │
        │  (Next.js App Router)    │
        ├─────────────────────────┤
        │  API Routes (/api/*)    │
        │  - RAG Chat              │
        │  - Catalog Search        │
        │  - Health Check          │
        ├─────────────────────────┤
        │  Page Routes             │
        │  - / (Home)              │
        │  - /chat                 │
        │  - /recommendations      │
        ├─────────────────────────┤
        │  External Services       │
        │  - Neon PostgreSQL       │
        │  - Upstash Redis         │
        │  - Upstash Vector        │
        │  - Google Gemini API     │
        └────────────────────────┘
```

#### 2.3 环境变量

**必需变量**：

```env
GOOGLE_API_KEY=<api-key>
DATABASE_URL=postgresql://...
UPSTASH_VECTOR_REST_URL=https://...
UPSTASH_VECTOR_REST_TOKEN=<token>
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=<token>
```

#### 2.4 部署清单

```bash
# 1. 在 Vercel Dashboard 导入仓库
# 2. 选择 bookstore-agentic-rag 目录
# 3. 配置环境变量
# 4. 连接 Neon、Upstash 集成
# 5. 部署
```

---

## 两项目间的数据协议

### 数据流向

```
bookstore-local-platform          bookstore-agentic-rag
     (Railway)                           (Vercel)
         │                                  │
         │ 1. 导出图书JSON                 │
         ├──────────────────────────────►  │
         │                                  │
         │                                  │ 2. 导入 Neon
         │                                  ├─────────────►
         │                                  │
         │  3. 共享 DATABASE_URL (Neon)    │
         │◄──────────────────────────────────┤
         │                                  │
         │  4. 推荐数据查询                 │
         │  (可选 CATALOG_SERVICE_URL)      │
         │◄──────────────────────────────────┤
```

### 协议规范

**阶段 1：数据初始化**
- bookstore-local-platform 运行 `scripts/export_books.py`
- 生成 `scripts/output/books.json`
- 手动或自动上传至 bookstore-agentic-rag
- bookstore-agentic-rag 运行 `npm run import:books` 导入 Neon

**阶段 2：运行时**
- bookstore-agentic-rag 直连 `DATABASE_URL`（Neon Postgres）
- bookstore-local-platform 也可直连相同 `DATABASE_URL`
- 不再通过 HTTP API 中转数据，直接数据库读写

**阶段 3：降级兜底**
- 如果 bookstore-agentic-rag 无法访问数据库
- 可选通过 `CATALOG_SERVICE_URL` 调用 bookstore-local-platform 的 `/api/v1/catalog/*`
- 但这是备选方案，不是首选

---

## 弃用的配置说明

### ⚠️ 以下文件/配置已过时，仅供参考

| 文件 | 原用途 | 状态 | 说明 |
|------|--------|------|------|
| `apps/bookstore-gateway/railway.toml` | 独立 gateway 服务部署 | 废弃 | 现在使用根目录 railway.toml |
| `apps/bookstore-auth/railway.toml` | 独立 auth 服务部署 | 废弃 | 现在 auth 功能在 gateway 中 |
| `apps/bookstore-gateway/support/deploy/fly.toml` | Fly.io 后端部署 | 备选 | 如需 Fly.io 部署可参考此配置 |
| `apps/bookstore-*/Dockerfile` | 微服务镜像构建 | 废弃 | 现在使用根目录 Dockerfile |

### 为什么弃用？

1. **简化架构**：从多服务改为单一 platform 服务
2. **成本优化**：Railway 免费额度内能支撑单服务
3. **运维简化**：一个域名、一个入口点
4. **部署速度**：减少跨服务部署时间

---

## 迁移指南

### 从旧多服务架构迁移

**旧架构（已废弃）**：
```
Railway:
  ├── auth (apps/bookstore-auth)
  ├── gateway (apps/bookstore-gateway)
  ├── catalog (apps/bookstore-catalog)
  └── ops (apps/bookstore-ops)
```

**新架构（推荐）**：
```
Railway:
  └── platform (root Dockerfile)
       ├── frontend dist
       └── backend (unified gateway)
```

### 迁移步骤

1. **创建新 Railway 项目**：`bookstore-platform`
2. **连接仓库根目录**
3. **复制环境变量**：从旧服务合并到新 platform
4. **部署验证**：确认所有功能正常
5. **流量切换**：更新 DNS 指向新域名
6. **清理**：删除旧的 Railway 服务

---

## 故障排查

### 部署失败

```bash
# 检查环境变量是否都已设置
railway variables list

# 检查日志
railway logs

# 重新部署
railway up --detach
```

### 前端无法访问 API

**原因 1**：CORS_ORIGINS 不匹配
```bash
railway variables get CORS_ORIGINS
# 应该是 https://<railroad-domain>，不能是 localhost
```

**原因 2**：后端未启动
```bash
curl -f https://<your-domain>/health
# 应该返回 200
```

### 数据库连接失败

```bash
# 检查 DATABASE_URL 格式
railway variables get DATABASE_URL

# 从 Railway 连接测试
railway connect postgres
```

---

## 安全建议

### 环境变量

- ✅ **使用强随机字符串**：`openssl rand -hex 32`
- ✅ **定期轮换**：特别是 JWT_SECRET_KEY 和 API 密钥
- ❌ **不要在代码中硬编码**
- ❌ **不要在 Git 中提交 .env**
- ❌ **不要在文档中暴露真实值**

### 网络

- ✅ **强制 HTTPS**：Railway 自动提供
- ✅ **配置 CORS 白名单**：具体域名而非 `*`
- ✅ **使用私有数据库连接**：PostgreSQL、Redis、Qdrant 都应在私有网络
- ❌ **不要暴露数据库公网访问**

### 认证

- ✅ **首次登录修改默认密码**
- ✅ **使用标准库**：python-jose（而不是自制 JWT）
- ✅ **密码哈希**：bcrypt（而不是 SHA-256）

---

## 性能优化

### 前端（bookstore-agentic-rag）

- 使用 Next.js 13+ App Router
- 启用静态站点生成 (SSG)
- 缓存策略：使用 Upstash Redis

### 后端（bookstore-local-platform）

- 使用 FastAPI 异步端点
- 连接池管理 PostgreSQL
- Redis 缓存推荐结果
- Qdrant 向量缓存

---

## 成本估算（2026 年参考价格）

| 服务 | 免费额度 | 超出成本 | 推荐配置 |
|------|---------|--------|---------|
| Railway | 5$/月 积分 | 0.000463$/分钟 | 单 platform 服务通常不超出 |
| Vercel | 免费 | 按流量计费 | Next.js 优化应用通常免费 |
| Neon PostgreSQL | 0.5 GiB 存储 | 每 GiB $0.15/月 | 通常免费额度足够 |
| Upstash Redis | 10,000 命令/天 | 每 100 万命令 $0.20 | 免费额度足够 |
| Qdrant Cloud | Free 集群 | 起价 $9/月 | 免费集群足够小规模应用 |

**总成本估算**：$0~15/月（取决于使用量）

---

## 相关文档

- [Railway 部署详细指南](./RAILWAY_DEPLOYMENT.md)
- [部署检查清单](./DEPLOY_GUIDE.md)
- [隐私和安全修复记录](./DEPLOYMENT_README.md)

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.0 | 2026-04-27 | 统一为单一 platform 服务，移除本地路径泄露 |
| 1.5 | 2026-03-15 | 添加 Fly.io 备选方案 |
| 1.0 | 2026-01-01 | 初始文档 |
