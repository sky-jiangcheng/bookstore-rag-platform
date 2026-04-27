# BookStore Platform - 部署摘要

## 部署目标

BookStore Local Platform 现在只部署一个 Railway `platform` 服务。根目录 `Dockerfile` 构建前端和后端，`main.py` 是唯一生产入口，`railway.toml` 直接指向这个 `Dockerfile`。

## 已完成

- [x] 创建单服务 Railway 配置
- [x] 将部署文档收敛为单一平台
- [x] 将 README 对齐到生产形态

## 待执行

- [ ] 安装 Railway CLI
- [ ] 登录 Railway 账户
- [ ] 部署单一平台服务
- [ ] 配置平台域名到下游系统
- [ ] 验证健康检查和核心 API

## 快速开始

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

### 3. 添加所需基础设施

```bash
railway add --plugin postgres
railway add --plugin redis
railway add --plugin qdrant
```

### 4. 配置环境变量

```bash
railway variables set JWT_SECRET_KEY="$(openssl rand -hex 32)"
railway variables set CORS_ORIGINS="https://<railway-domain>"
railway variables set GEMINI_API_KEY="your-actual-api-key"
```

### 5. 部署单服务平台

```bash
railway up
railway domains
```

部署后只会有一个平台域名。下游系统如果需要访问这套服务，只要指向这个单一域名即可。

## 文件清单

| 文件 | 说明 |
|------|------|
| `railway.toml` | 单服务 Railway 配置，指向根目录 `Dockerfile` |
| `Dockerfile` | 前后端一体镜像构建 |
| `main.py` | 生产入口 |
| `DEPLOYMENT_README.md` | 面向部署执行的简版说明 |
| `RAILWAY_DEPLOYMENT.md` | 详细部署指南 |

## 验证

```bash
curl -f https://<railway-domain>/health
```

再确认登录、推荐、书单生成和导出流程都能在同一个域名下完成。

## 备注

- 旧的多服务 Railway 域名和服务名不再作为默认文档。
- `apps/` 下的模块仅作为仓库内部实现，不再代表独立部署单位。
