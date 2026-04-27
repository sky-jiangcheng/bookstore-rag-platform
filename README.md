# BookStore README

这是 BookStore 的单服务平台仓库。生产形态由根目录 `Dockerfile` 构建，`main.py` 作为唯一对外入口，把前端和后端收敛到同一个 Railway `platform` 服务里。

## 生产形态

- `main.py` - 单入口平台，生产运行时直接启动它
- `Dockerfile` - 根目录统一镜像构建，包含前端构建产物和后端依赖
- `railway.toml` - 单服务 Railway 配置，指向根目录 `Dockerfile`

## 仓库内容

- `apps/bookstore-frontend` - 前端页面与静态资源
- `apps/bookstore-gateway` - 平台共享后端代码
- `apps/bookstore-auth` - 历史认证模块，保留为内部代码
- `apps/bookstore-rag` - 历史推荐模块，保留为内部代码
- `apps/bookstore-catalog` - 历史目录能力，保留为内部代码
- `apps/bookstore-ops` - 历史运营能力，保留为内部代码

## 运行原则

- 生产只保留一个对外入口和一个 Railway 服务
- 前端静态资源与后端 API 同域
- 旧模块只保留在仓库里，不再作为独立部署目标

## 本地启动

```bash
cd bookstore-local-platform
uvicorn main:app --reload --port 8000
```

## 与线上项目的关系

- 本仓库负责平台侧的登录、推荐、书单生成和导出
- 线上部署只暴露单一平台域名，不再依赖多服务转发
- `bookstore-agentic-rag` 仍可作为其他项目的独立消费端

## 数据导出

推荐通过文件导出，而不是直接共享数据库连接。

```bash
cd bookstore-local-platform
export LEGACY_DATABASE_URL="sqlite:///path/to/bookstore.db"
python3 scripts/export_books.py
```

默认输出文件：

- `scripts/output/books.json`

## 快速开始

### 1. 环境准备

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入你的配置
# 特别是这些必需项:
# - JWT_SECRET_KEY: openssl rand -hex 32
# - DATABASE_URL: 数据库连接字符串
# - GEMINI_API_KEY: AI 模型 API 密钥
```

### 2. 本地开发

```bash
# 安装前端依赖
cd apps/bookstore-frontend
npm install
npm run build

# 返回项目根目录
cd ../..

# 启动后端
pip install -r apps/bookstore-gateway/requirements.txt
uvicorn main:app --reload --port 8000

# 访问 http://localhost:8000
```

### 3. 部署到 Railway

详见 [DEPLOYMENT_ARCHITECTURE.md](./DEPLOYMENT_ARCHITECTURE.md) 和 [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

```bash
# 1. 安装 Railway CLI
npm install -g @railway/cli

# 2. 登录
railway login

# 3. 初始化项目
railway init --name bookstore-platform

# 4. 配置资源和环境变量
# 见部署文档

# 5. 部署
railway up
```

## 文档

- 📋 [部署架构说明](./DEPLOYMENT_ARCHITECTURE.md) - 推荐阅读！
- 🚀 [Railway 部署指南](./RAILWAY_DEPLOYMENT.md)
- 📖 [完整部署指南](./DEPLOY_GUIDE.md)
- 🔐 [安全最佳实践](#安全最佳实践)

## 安全最佳实践

### 环境变量

✅ **必做**：

```bash
# 生成强随机 JWT 密钥
openssl rand -hex 32

# 从不在代码中硬编码敏感信息
# 使用 .env 本地开发，Railway Secrets 生产部署
```

❌ **禁止**：

- 不要提交 `.env` 文件到 Git
- 不要在 README 或文档中暴露真实 API 密钥
- 不要使用弱密码作为 ADMIN_PASSWORD

### 部署

- ✅ 强制使用 HTTPS（Railway 自动提供）
- ✅ 配置 CORS 白名单（具体域名，不用 `*`）
- ✅ 首次登录后修改默认管理员密码
- ✅ 定期轮换 JWT_SECRET_KEY 和 API 密钥

## 故障排查

### 服务无法启动

```bash
# 检查环境变量
railway variables list

# 查看日志
railway logs

# 重新部署
railway up --detach
```

### 前端无法访问 API

1. 检查 `CORS_ORIGINS` 是否包含当前域名
2. 检查浏览器控制台是否有 CORS 错误
3. 确认后端服务是否正常运行

### 数据库连接失败

```bash
# 测试连接
railway connect postgres

# 检查连接字符串
railway variables get DATABASE_URL
```

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue 3 | 3.x |
| 后端框架 | FastAPI | 0.100+ |
| 数据库 | PostgreSQL | 13+ |
| 向量DB | Qdrant | 1.x |
| 缓存 | Redis | 6.0+ |
| 部署 | Railway | - |

## 许可证

MIT

## 支持

遇到问题？检查这些资源：

1. [DEPLOYMENT_ARCHITECTURE.md](./DEPLOYMENT_ARCHITECTURE.md) - 架构与部署问题
2. [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) - Railway 特定问题
3. [.env.example](./.env.example) - 环境变量配置问题
