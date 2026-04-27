#!/bin/bash

# BookStore Platform - 快速部署脚本
# 将本地服务部署到 Railway，并更新 Vercel 环境变量

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  BookStore Platform - 快速部署        ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# 项目路径（自动检测）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$PLATFORM_DIR")"
AGENTIC_DIR="$PROJECT_ROOT/bookstore-agentic-rag"
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}  安装 Railway CLI...${NC}"
    npm install -g @railway/cli
fi
echo -e "${GREEN}  ✓ Railway CLI 已就绪${NC}"

# 登录 Railway
echo ""
echo -e "${YELLOW}[2/6] 登录 Railway...${NC}"
railway login
echo -e "${GREEN}  ✓ 登录成功${NC}"

# 初始化 Railway 项目
echo ""
echo -e "${YELLOW}[3/6] 初始化 Railway 项目...${NC}"
railway init --name bookstore-local-platform --force
echo -e "${GREEN}  ✓ 项目初始化完成${NC}"

# 添加基础设施
echo ""
echo -e "${YELLOW}[4/6] 添加基础设施...${NC}"

# 检查是否已有 PostgreSQL
if ! railway list --plugins | grep -q "postgres"; then
    railway add --plugin postgres
    echo -e "${GREEN}  ✓ PostgreSQL 已添加${NC}"
else
    echo -e "${GREEN}  ✓ PostgreSQL 已存在${NC}"
fi

# 检查是否已有 Redis
if ! railway list --plugins | grep -q "redis"; then
    railway add --plugin redis
    echo -e "${GREEN}  ✓ Redis 已添加${NC}"
else
    echo -e "${GREEN}  ✓ Redis 已存在${NC}"
fi

# 配置环境变量
echo ""
echo -e "${YELLOW}[5/6] 配置环境变量...${NC}"
railway variables set JWT_SECRET_KEY="$(openssl rand -hex 32)" 2>/dev/null || true
railway variables set CORS_ORIGINS="https://bookstore-agentic-rag.vercel.app" 2>/dev/null || true
railway variables set LOG_LEVEL="INFO" 2>/dev/null || true
echo -e "${GREEN}  ✓ 环境变量已配置${NC}"

# 部署服务
echo ""
echo -e "${YELLOW}[6/6] 部署服务...${NC}"

SERVICES=("gateway" "auth" "catalog" "ops")
DOMAINS_FILE="/tmp/railway_domains.txt"

echo "" > "$DOMAINS_FILE"

for service in "${SERVICES[@]}"; do
    echo -e "  部署 ${service}..."

    # 检查服务是否已存在
    if railway list | grep -q "$service"; then
        echo -e "    ${YELLOW}服务已存在，跳过创建${NC}"
    else
        # 创建服务
        railway create --name "$service" 2>/dev/null || true
    fi

    # 设置服务根目录
    railway variables set SERVICE_ROOT="apps/bookstore-$service" 2>/dev/null || true

    # 部署
    echo -e "    ${BLUE}正在部署 ${service}...${NC}"
    railway up --service "$service" --detach 2>/dev/null || true

    # 等待服务启动
    sleep 2
done

echo -e "${GREEN}  ✓ 所有服务已部署${NC}"

# 获取服务域名
echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  服务信息                          ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "服务域名："
railway domains | tee "$DOMAINS_FILE"

# 提取域名
GATEWAY_URL=$(grep "gateway" "$DOMAINS_FILE" | head -1 | awk '{print $2}')
AUTH_URL=$(grep "auth" "$DOMAINS_FILE" | head -1 | awk '{print $2}')
CATALOG_URL=$(grep "catalog" "$DOMAINS_FILE" | head -1 | awk '{print $2}')
OPS_URL=$(grep "ops" "$DOMAINS_FILE" | head -1 | awk '{print $2}')

# 生成 Vercel 环境变量
echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  下一步操作                          ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "1. 在 Vercel 项目中添加以下环境变量："
echo ""
echo -e "${YELLOW}GATEWAY_URL=${GATEWAY_URL}${NC}"
echo -e "${YELLOW}AUTH_URL=${AUTH_URL}${NC}"
echo -e "${YELLOW}CATALOG_URL=${CATALOG_URL}${NC}"
echo -e "${YELLOW}OPS_URL=${OPS_URL}${NC}"
echo ""
echo -e "2. 重新部署 Vercel 项目："
echo -e "${YELLOW}cd $AGENTIC_DIR && vercel --prod${NC}"
echo ""
echo -e "3. 测试服务连接："
echo -e "${YELLOW}curl ${GATEWAY_URL}/health${NC}"
echo ""
echo -e "4. 查看日志："
echo -e "${YELLOW}railway logs --service gateway${NC}"
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  部署完成！                          ${NC}"
echo -e "${GREEN}=========================================${NC}"

# 清理临时文件
rm -f "$DOMAINS_FILE"
