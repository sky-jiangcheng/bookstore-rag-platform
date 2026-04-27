# BookStore 项目部署指南

## 项目概述

本项目包含两个独立项目，职责强隔离：

1. **bookstore-agentic-rag** - 面向 Vercel 部署的核心项目
   - Agentic RAG 对话式图书推荐
   - Next.js 前端体验
   - API / SSE / 编排层
   - Upstash Vector / Redis 集成
   - Neon Postgres 主数据访问

2. **bookstore-local-platform** - 本地/云端部署的后台管理平台
   - 单服务架构（platform）
   - FastAPI + Vue3 前后端一体
   - Railway 部署支持

---

## 一、bookstore-local-platform 部署（推荐 Railway）

### 1.1 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                      Railway                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  platform (single web service)                  │  │
│  │  - Dockerfile 构建前后端一体镜像               │  │
│  │  - main.py 是生产入口                          │  │
│  │  - 一个公开域名                                │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Private resources                              │  │
│  │  - PostgreSQL / SQLite                          │  │
│  │  - Redis / Upstash Redis                        │  │
│  │  - Qdrant                                       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 必要环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `APP_ENV` | 运行环境，设为 `free_cloud` | ✅ |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产环境必须设置） | ✅ |
| `CORS_ORIGINS` | 允许的跨域来源 | ✅ |
| `DATABASE_URL` | 数据库连接串（PostgreSQL/SQLite） | ✅ |
| `QDRANT_URL` | Qdrant 向量数据库地址 | ✅ |
| `QDRANT_API_KEY` | Qdrant API 密钥 | 可选 |
| `UPSTASH_REDIS_URL` | Redis 连接串 | 可选 |
| `ADMIN_PASSWORD` | 管理员初始密码 | ✅ |
| `GEMINI_API_KEY` | AI 模型 API 密钥（至少配置一个） | ✅ |

### 1.3 部署步骤

#### 方式一：Railway CLI 部署（推荐）

```bash
# 1. 安装 Railway CLI
npm install -g @railway/cli
# 或
brew install railwaycli

# 2. 登录 Railway
railway login

# 3. 进入项目目录
cd bookstore-local-platform

# 4. 初始化项目（首次部署）
railway init --name bookstore-platform

# 5. 添加基础设施资源
railway add --plugin postgres    # 或使用 SQLite
railway add --plugin redis       # 或使用 Upstash
railway add --plugin qdrant      # 向量数据库

# 6. 配置环境变量
railway variables set APP_ENV="free_cloud"
railway variables set JWT_SECRET_KEY="$(openssl rand -hex 32)"
railway variables set ADMIN_PASSWORD="your-secure-password"
railway variables set GEMINI_API_KEY="your-gemini-api-key"

# 7. 部署
railway up

# 8. 获取域名
railway domains
```

#### 方式二：Railway Dashboard 部署

1. 访问 [Railway Dashboard](https://railway.app/dashboard)
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择 `bookstore-local-platform` 目录
4. 添加必要资源：PostgreSQL、Redis、Qdrant
5. 在 Variables 中设置上述环境变量
6. 点击 Deploy

### 1.4 验证部署

```bash
# 检查健康状态
curl https://<your-domain>/health

# 预期响应
{"status":"healthy","service":"platform"}
```

### 1.5 访问应用

部署成功后，访问 Railway 分配的域名即可：
- 前端页面：`https://<your-domain>/`
- 认证页面：`https://<your-domain>/auth.html`
- RAG 推荐：`https://<your-domain>/rag.html`
- API 文档：`https://<your-domain>/docs`

---

## 二、bookstore-agentic-rag 部署（Vercel）

### 2.1 部署步骤

```bash
# 1. 进入项目目录
cd bookstore-agentic-rag

# 2. 安装依赖
npm install

# 3. 配置环境变量（.env.local）
cp .env.example .env.local
# 编辑 .env.local 填入必要的 API 密钥

# 4. 本地测试
npm run dev

# 5. 部署到 Vercel
vercel --prod
```

### 2.2 必要环境变量

| 变量名 | 说明 |
|--------|------|
| `UPSTASH_REDIS_REST_URL` | Upstash Redis URL |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash Redis Token |
| `UPSTASH_VECTOR_REST_URL` | Upstash Vector URL |
| `UPSTASH_VECTOR_REST_TOKEN` | Upstash Vector Token |
| `DATABASE_URL` | Neon Postgres URL |
| `GEMINI_API_KEY` | Google Gemini API Key |

---

## 三、安全注意事项

### 3.1 生产环境必做

1. **设置强 JWT 密钥**
   ```bash
   openssl rand -hex 32
   ```

2. **修改默认管理员密码**
   - 首次登录后立即修改

3. **启用 HTTPS**
   - Railway 自动提供 HTTPS
   - 确保 `CORS_ORIGINS` 使用 HTTPS URL

4. **配置 CORS 白名单**
   - 不要设置为 `*`
   - 只添加信任的域名

### 3.2 已修复的安全问题

根据 2026-04-27 的安全审计，以下问题已修复：

- ✅ 密码哈希从 SHA-256 升级到 bcrypt
- ✅ JWT 从自制方案升级到 python-jose 标准
- ✅ 修复数据库连接泄漏
- ✅ 移除硬编码 JWT 密钥
- ✅ 加固降级认证机制
- ✅ 移除测试数据污染

---

## 四、故障排查

### 4.1 服务无法启动

```bash
# 查看日志
railway logs

# 检查环境变量
railway variables list
```

### 4.2 数据库连接失败

```bash
# 测试数据库连接
railway connect postgres

# 检查 DATABASE_URL
railway variables get DATABASE_URL
```

### 4.3 前端无法访问 API

1. 检查 `CORS_ORIGINS` 是否包含当前域名
2. 检查浏览器控制台是否有 CORS 错误
3. 确认后端服务健康状态

### 4.4 向量搜索无结果

1. 检查 Qdrant 连接状态
2. 确认书籍数据已导入向量库
3. 查看日志中的向量服务初始化信息

---

## 五、维护与更新

### 5.1 更新部署

```bash
# 代码更新后重新部署
git add .
git commit -m "更新内容"
git push

# Railway 会自动触发重新部署
```

### 5.2 备份数据

```bash
# 数据库备份
railway connect postgres
# 使用 pg_dump 导出数据

# 向量数据备份
# 通过 Qdrant API 导出集合快照
```

---

## 六、相关文档

- [Railway 官方文档](https://docs.railway.app/)
- [Vercel 部署文档](https://vercel.com/docs)
- [项目安全修复报告](./SECURITY_FIX_REPORT.md)
- [Railway 部署详细指南](./RAILWAY_DEPLOYMENT.md)

---

## 七、快速检查清单

部署前确认：

- [ ] `JWT_SECRET_KEY` 已设置为强随机字符串
- [ ] `ADMIN_PASSWORD` 已设置为安全密码
- [ ] `CORS_ORIGINS` 已配置正确的域名
- [ ] `DATABASE_URL` 指向正确的数据库
- [ ] `QDRANT_URL` 指向正确的向量数据库
- [ ] 至少配置了一个 AI 模型 API 密钥
- [ ] `APP_ENV` 设置为 `free_cloud`

部署后验证：

- [ ] `/health` 返回 healthy
- [ ] 登录接口正常工作
- [ ] 推荐接口返回结果
- [ ] 前端页面正常加载
