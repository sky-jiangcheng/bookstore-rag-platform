#!/bin/bash

# Railway 部署脚本
# BookStore Local Platform - Railway Deployment

set -e

echo "========================================="
echo "BookStore Local Platform - Railway 部署"
echo "========================================="

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Railway CLI 是否已安装
if ! command -v railway &> /dev/null; then
    echo "${YELLOW}Railway CLI 未安装，正在安装...${NC}"
    npm install -g @railway/cli
    echo "${GREEN}Railway CLI 安装完成${NC}"
fi

# 登录 Railway
echo "${YELLOW}请登录 Railway 账户...${NC}"
railway login

# 创建项目
echo "${YELLOW}创建 Railway 项目...${NC}"
railway init --name bookstore-local-platform

# 添加 PostgreSQL
echo "${YELLOW}添加 PostgreSQL 数据库...${NC}"
railway add postgres

# 添加 Redis
echo "${YELLOW}添加 Redis 缓存...${NC}"
railway add redis

# 添加 Qdrant（使用 Docker 插件）
echo "${YELLOW}添加 Qdrant 向量数据库...${NC}"
railway add plugin --image qdrant/qdrant:latest

# 设置环境变量
echo "${YELLOW}配置环境变量...${NC}"
railway variables set JWT_SECRET_KEY="$(openssl rand -hex 32)"
railway variables set CORS_ORIGINS="https://bookstore-agentic-rag.vercel.app"
railway variables set LOG_LEVEL="INFO"

# 部署各服务
SERVICES=("gateway" "auth" "catalog" "ops")

for service in "${SERVICES[@]}"; do
    echo "${YELLOW}部署 $service 服务...${NC}"

    # 创建服务
    railway create --services "$service"

    # 设置服务根目录
    railway variables set SERVICE_ROOT="apps/bookstore-$service"

    # 链接数据库和缓存
    railway link postgres
    railway link redis
    railway link qdrant

    # 部署
    railway up --service "$service"
done

echo "${GREEN}=========================================${NC}"
echo "${GREEN}部署完成！${NC}"
echo "${GREEN}=========================================${NC}"
echo ""
echo "获取服务域名..."
railway domains

echo ""
echo "下一步："
echo "1. 记录各服务的域名"
echo "2. 更新 Vercel 项目的环境变量"
echo "3. 测试服务连接"
echo ""
echo "查看日志: railway logs --service <service-name>"
echo "查看状态: railway status"
