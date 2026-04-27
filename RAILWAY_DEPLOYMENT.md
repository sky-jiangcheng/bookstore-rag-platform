# BookStore Local Platform - Railway 部署指南

## 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                      Railway                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  platform (single web service)                  │  │
│  │  - root Dockerfile builds frontend + backend   │  │
│  │  - main.py is the production entrypoint        │  │
│  │  - one public domain                            │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Private resources                              │  │
│  │  - PostgreSQL                                   │  │
│  │  - Redis                                        │  │
│  │  - Qdrant                                       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 快速部署步骤

### 1. 安装 Railway CLI

```bash
npm install -g @railway/cli
# 或
brew install railwaycli
railway --version
```

### 2. 登录并初始化项目

```bash
railway login
cd /Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform
railway init --name bookstore-local-platform
```

### 3. 添加基础设施

```bash
railway add --plugin postgres
railway add --plugin redis
railway add --plugin qdrant
```

### 4. 配置环境变量

```bash
railway variables set JWT_SECRET_KEY="$(openssl rand -hex 32)"
railway variables set CORS_ORIGINS="https://<railway-domain>"
railway variables set APP_ENV="free_cloud"
railway variables set GEMINI_API_KEY="your-api-key"
```

`railway.toml` 已经在仓库根目录指向 `Dockerfile`，所以不需要再配置单独的服务根目录。

### 5. 部署单一平台服务

```bash
railway up
railway domains
```

只会得到一个公开域名，对外流量都走这个 `platform` 服务。

### 6. 验证部署

```bash
curl -f https://<railway-domain>/health
```

再确认登录、推荐、书单生成和导出都能在同一个域名下工作。

## 环境变量参考

| 变量名 | 说明 |
|--------|------|
| `APP_ENV` | 平台运行环境，通常设为 `free_cloud` |
| `CORS_ORIGINS` | 允许访问的平台域名 |
| `DATABASE_URL` | PostgreSQL 连接串 |
| `QDRANT_URL` | Qdrant 地址 |
| `QDRANT_API_KEY` | Qdrant API key |
| `UPSTASH_REDIS_URL` | Redis 连接串 |
| `JWT_SECRET_KEY` | JWT 密钥 |
| `ADMIN_PASSWORD` | 管理员密码 |
| `GEMINI_API_KEY` | 模型密钥示例 |

## 维护和排查

### 查看状态

```bash
railway status
railway logs
```

### 服务无法启动

```bash
railway variables list
railway up --detach
```

### 数据库连接失败

```bash
railway connect postgres
railway variables get DATABASE_URL
```

## 相关文档

- [Railway 官方文档](https://docs.railway.app/)
- [Railway Python 部署指南](https://docs.railway.app/deploy/python)
- [Railway 环境变量](https://docs.railway.app/develop/variables)
