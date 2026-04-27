# 🚀 BookStore 系统启动与观察指南

## ✅ 当前运行的服务

### Docker 容器服务
```
bookstore-mysql   :3306    MySQL数据库
bookstore-redis   :6379    Redis缓存
bookstore-qdrant  :6333    向量数据库
```

### 本地服务
```
Backend (FastAPI) :8000    后端API服务
```

---

## 📊 如何观察各个服务

### 1️⃣ **后端 API 服务** (FastAPI) - http://localhost:8000

#### 健康检查
```bash
# 快速检查服务是否在线
curl http://localhost:8000/health
```

**预期响应:**
```json
{
  "status": "healthy"
}
```

#### 就绪状态
```bash
# 检查所有依赖项是否就绪（数据库、缓存、向量DB）
curl http://localhost:8000/ready
```

#### API 文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### 监控指标 (Prometheus)
```bash
# 获取所有系统指标
curl http://localhost:8000/metrics | head -50
```

**关键指标:**
```
# 请求延迟分布
http_request_duration_seconds_bucket
http_request_duration_seconds_count

# 错误率
http_requests_total{status="500"}

# 缓存命中率
cache_hits_total / cache_total

# LLM API调用
llm_api_calls_total{provider="gemini"}

# 向量查询性能
vector_query_duration_seconds
```

#### 查看日志
```bash
# 查看后端运行日志
tail -f logs/app.log

# 搜索特定错误
grep "ERROR" logs/app.log | tail -20

# JSON格式日志
tail -f logs/app.log | jq '.'
```

---

### 2️⃣ **MySQL 数据库** - localhost:3306

#### 检查连接
```bash
# 连接到MySQL
docker exec -it bookstore-mysql mysql -u root bookstore

# 查看表结构
SHOW TABLES;
SELECT * FROM t_user LIMIT 5;
SELECT COUNT(*) FROM t_book_info;
SELECT COUNT(*) FROM t_custom_book_list;
```

#### 常用命令
```sql
-- 查看数据库大小
SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.tables 
WHERE table_schema = 'bookstore';

-- 查看最近的书单请求
SELECT id, user_id, status, created_at FROM t_custom_book_list ORDER BY created_at DESC LIMIT 10;

-- 查看用户行为
SELECT COUNT(*) FROM t_user_behavior;
SELECT action_type, COUNT(*) FROM t_user_behavior GROUP BY action_type;
```

---

### 3️⃣ **Redis 缓存** - localhost:6379

#### 检查缓存状态
```bash
# 连接到Redis
docker exec -it bookstore-redis redis-cli

# 基本命令
PING                    # 测试连接
INFO                    # 查看Redis统计信息
DBSIZE                  # 查看缓存大小
KEYS *                  # 列出所有缓存键
GET <key>              # 查看缓存值
FLUSHDB                # 清除当前库（谨慎使用）
```

#### 性能监控
```bash
# 查看命令延迟统计
LATENCY LATEST          # 最近的延迟事件
LATENCY HISTOGRAM       # 延迟直方图

# 内存使用
INFO memory

# 命中率
INFO stats              # 查看 hits 和 misses
```

---

### 4️⃣ **Qdrant 向量数据库** - http://localhost:6333

#### Web UI (向量数据库管理界面)
```
http://localhost:6333/dashboard
```

#### API 检查
```bash
# 查看集合列表
curl http://localhost:6333/collections

# 查看具体集合信息
curl http://localhost:6333/collections/bookstore

# 集合统计
curl http://localhost:6333/collections/bookstore/stats
```

**预期响应示例:**
```json
{
  "result": {
    "name": "bookstore",
    "points_count": 1500,
    "vectors_count": 1500,
    "status": "green"
  }
}
```

---

## 🔍 完整的系统监控流程

### 第1步: 验证所有服务在线
```bash
# 后端健康检查
curl -s http://localhost:8000/health | jq '.status'

# MySQL检查
docker exec bookstore-mysql mysql -u root bookstore -e "SELECT 1;" 2>/dev/null && echo "MySQL: ✅"

# Redis检查
docker exec bookstore-redis redis-cli PING 2>/dev/null && echo "Redis: ✅"

# Qdrant检查
curl -s http://localhost:6333/collections | jq '.status' | grep -q "success" && echo "Qdrant: ✅"
```

### 第2步: 监控实时流量
```bash
# 终端1: 查看Prometheus指标
watch -n 2 'curl -s http://localhost:8000/metrics | grep -E "^(http_|llm_|cache_)" | head -20'

# 终端2: 查看实时日志
tail -f logs/app.log | jq '.message, .level' 2>/dev/null

# 终端3: 监控数据库
docker exec -it bookstore-mysql mysql -u root bookstore -e "SELECT COUNT(*) as book_count FROM t_book_info; SELECT COUNT(*) as request_count FROM t_custom_book_list;"
```

### 第3步: 测试关键API
```bash
# 1. 登录获取token
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# 2. 调用推荐API
curl -s -X POST http://localhost:8000/v1/book-list/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement":"我需要学习Python编程"}' | jq '.'

# 3. 查看缓存
curl -s http://localhost:8000/metrics | grep cache_

# 4. 查看性能指标
curl -s http://localhost:8000/metrics | grep http_request_duration
```

---

## 📈 关键监控指标说明

| 指标 | 说明 | 正常范围 |
|------|------|---------|
| `http_request_duration_seconds` | API响应时间 | < 1s |
| `http_requests_total{status="500"}` | 错误请求 | = 0 |
| `cache_hit_ratio` | 缓存命中率 | > 70% |
| `llm_api_calls_total` | LLM调用次数 | 持续增长 |
| `vector_query_duration_seconds` | 向量查询延迟 | < 200ms |
| `database_connection_pool_active` | 数据库连接数 | < 20 |

---

## 🛠️ 常见排查步骤

### API 服务无响应
```bash
# 1. 检查进程
ps aux | grep uvicorn

# 2. 查看日志错误
tail -100 logs/app.log | grep ERROR

# 3. 检查依赖
curl http://localhost:8000/ready

# 4. 重启服务
kill <pid> && cd backend/services/gateway && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 缓存不生效
```bash
# 1. 检查Redis是否运行
docker ps | grep redis

# 2. 清除缓存
docker exec bookstore-redis redis-cli FLUSHDB

# 3. 检查缓存连接
curl -s http://localhost:8000/health | jq '.dependencies'
```

### 向量查询慢
```bash
# 1. 检查Qdrant状态
curl http://localhost:6333/health

# 2. 查看集合大小
curl http://localhost:6333/collections/bookstore/stats

# 3. 检查网络延迟
time curl http://localhost:6333/collections > /dev/null
```

### 数据库问题
```bash
# 1. 检查表是否存在
docker exec bookstore-mysql mysql -u root bookstore -e "SHOW TABLES;"

# 2. 检查数据量
docker exec bookstore-mysql mysql -u root bookstore -e "SELECT table_name, TABLE_ROWS FROM information_schema.TABLES WHERE table_schema='bookstore';"

# 3. 修复连接问题
# 重启MySQL
docker restart bookstore-mysql
```

---

## 📱 Dashboard & UI 地址

| 服务 | 地址 | 说明 |
|------|------|------|
| FastAPI Docs | http://localhost:8000/docs | 可交互的API文档 |
| ReDoc | http://localhost:8000/redoc | API参考文档 |
| Prometheus指标 | http://localhost:8000/metrics | 普罗米修斯格式 |
| Qdrant Dashboard | http://localhost:6333/dashboard | 向量数据库管理 |
| Redis CLI | `docker exec bookstore-redis redis-cli` | 命令行工具 |
| MySQL CLI | `docker exec bookstore-mysql mysql -u root` | 数据库CLI |

---

## 🔐 认证说明

所有 API 端点都需要认证:

```bash
# 1. 登录获取 Token
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# 2. 在请求头中使用 Token
curl -H "Authorization: Bearer <your_token>" \
  http://localhost:8000/v1/book-list/templates
```

---

## 📝 日志位置

```
后端日志:     logs/app.log         (JSON格式)
MySQL日志:   docker logs bookstore-mysql
Redis日志:   docker logs bookstore-redis
Qdrant日志:  docker logs bookstore-qdrant
```

---

## 🎯 快速启动检查清单

```bash
# 一键验证所有服务
echo "=== 服务健康检查 ===" && \
echo "后端: $(curl -s http://localhost:8000/health | jq '.status')" && \
echo "MySQL: $(docker exec bookstore-mysql mysql -u root -e 'SELECT 1;' 2>/dev/null && echo 'OK' || echo 'FAIL')" && \
echo "Redis: $(docker exec bookstore-redis redis-cli PING 2>/dev/null)" && \
echo "Qdrant: $(curl -s http://localhost:6333/health | jq '.status')"
```

---

**所有服务已启动，系统可用！** 🎉
