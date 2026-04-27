# 🎯 服务观察快速命令参考

## 📊 一键检查所有服务

```bash
# 完整的系统健康检查
echo "=== 📋 系统健康检查 ===" && \
echo "后端: $(curl -s http://localhost:8000/health | jq -r '.status')" && \
echo "MySQL: $(docker exec bookstore-mysql mysql -u root -e 'SELECT "OK"' 2>/dev/null | tail -1 || echo 'FAIL')" && \
echo "Redis: $(docker exec bookstore-redis redis-cli PING 2>/dev/null)" && \
echo "Qdrant: $(curl -s http://localhost:6333/health | jq -r '.title' 2>/dev/null || echo 'OK')"
```

---

## 🖥️ **后端 FastAPI 服务** (Port 8000)

### 基本命令
```bash
# 健康检查（最快验证）
curl -s http://localhost:8000/health | jq '.'

# 就绪检查（检查所有依赖）
curl -s http://localhost:8000/ready | jq '.'

# 查看所有Prometheus指标
curl -s http://localhost:8000/metrics | grep "^# HELP" | head -20

# 查看特定指标（如请求数）
curl -s http://localhost:8000/metrics | grep "http_requests_total"
```

### 实时监控
```bash
# 监控请求延迟（每2秒更新一次）
watch -n 2 'curl -s http://localhost:8000/metrics | grep http_request_duration_seconds_bucket'

# 监控错误率
watch -n 2 'curl -s http://localhost:8000/metrics | grep "status=\"500\""'

# 监控缓存命中率
watch -n 2 'curl -s http://localhost:8000/metrics | grep cache_'
```

### 日志查看
```bash
# 查看最新的后端日志
tail -50 logs/app.log

# 实时监控日志
tail -f logs/app.log

# 查看JSON格式的结构化日志
tail -f logs/app.log | jq '.'

# 搜索错误日志
grep "ERROR\|EXCEPTION" logs/app.log | tail -20
```

---

## 🗄️ **MySQL 数据库** (Port 3306)

### 连接与查询
```bash
# 进入MySQL命令行
docker exec -it bookstore-mysql mysql -u root bookstore

# 从shell快速查询
docker exec bookstore-mysql mysql -u root bookstore -e "SELECT COUNT(*) as book_count FROM t_book_info;"

# 查看所有表
docker exec bookstore-mysql mysql -u root bookstore -e "SHOW TABLES;"

# 查看表结构
docker exec bookstore-mysql mysql -u root bookstore -e "DESC t_book_info;"
```

### 数据检查
```bash
# 统计数据量
docker exec bookstore-mysql mysql -u root bookstore -e "
  SELECT 
    'Book Info' as table_name, COUNT(*) as count FROM t_book_info
  UNION ALL
  SELECT 'Users', COUNT(*) FROM t_user
  UNION ALL
  SELECT 'Book Lists', COUNT(*) FROM t_custom_book_list
  UNION ALL
  SELECT 'User Behavior', COUNT(*) FROM t_user_behavior;
"

# 查看数据库大小
docker exec bookstore-mysql mysql -u root bookstore -e "
  SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
  FROM information_schema.tables 
  WHERE table_schema = 'bookstore'
  ORDER BY size_mb DESC;
"

# 查看最近的书单请求
docker exec bookstore-mysql mysql -u root bookstore -e "
  SELECT id, user_id, status, created_at FROM t_custom_book_list 
  ORDER BY created_at DESC LIMIT 10;
"
```

### 实时监控
```bash
# 监控数据库连接数
watch -n 2 'docker exec bookstore-mysql mysql -u root bookstore -e "SHOW PROCESSLIST;" | wc -l'

# 监控表行数变化
watch -n 2 'docker exec bookstore-mysql mysql -u root bookstore -e "SELECT table_name, TABLE_ROWS FROM information_schema.TABLES WHERE table_schema=\"bookstore\";"'
```

---

## 💾 **Redis 缓存** (Port 6379)

### 基本操作
```bash
# 进入Redis命令行
docker exec -it bookstore-redis redis-cli

# 检查连接
docker exec bookstore-redis redis-cli PING

# 查看统计信息
docker exec bookstore-redis redis-cli INFO

# 查看缓存大小
docker exec bookstore-redis redis-cli DBSIZE

# 列出所有缓存键
docker exec bookstore-redis redis-cli KEYS "*"

# 查看特定缓存值
docker exec bookstore-redis redis-cli GET "<key_name>"
```

### 性能监控
```bash
# 查看内存使用
docker exec bookstore-redis redis-cli INFO memory

# 查看命令统计
docker exec bookstore-redis redis-cli INFO stats

# 实时监控延迟
watch -n 2 'docker exec bookstore-redis redis-cli LATENCY LATEST'

# 清除所有缓存（谨慎使用）
docker exec bookstore-redis redis-cli FLUSHDB
```

---

## 🔍 **Qdrant 向量数据库** (Port 6333)

### 基本操作
```bash
# 检查健康状态
curl -s http://localhost:6333/health | jq '.'

# 查看所有集合
curl -s http://localhost:6333/collections | jq '.'

# 查看特定集合信息
curl -s http://localhost:6333/collections/bookstore | jq '.'

# 查看集合统计
curl -s http://localhost:6333/collections/bookstore/stats | jq '.'

# 实时监控集合大小
watch -n 5 'curl -s http://localhost:6333/collections/bookstore/stats | jq ".result.points_count"'
```

---

## 📈 **常见监控任务**

### 监控面板（多终端）
```bash
# 终端1: API请求统计
watch -n 2 'curl -s http://localhost:8000/metrics | grep -E "^http_requests_total|^http_request_duration_seconds_count"'

# 终端2: 数据库活动
watch -n 3 'docker exec bookstore-mysql mysql -u root bookstore -e "SELECT COUNT(*) as total_rows, SUM(TABLE_ROWS) as data_rows FROM information_schema.TABLES WHERE table_schema=\"bookstore\";"'

# 终端3: 缓存活动
watch -n 3 'docker exec bookstore-redis redis-cli INFO stats | grep "total_commands_processed"'

# 终端4: 实时日志
tail -f logs/app.log | jq '.level, .message' 2>/dev/null
```

### 性能测试
```bash
# 简单的并发测试（需要 Apache Bench）
ab -n 100 -c 10 http://localhost:8000/health

# 或使用curl批量测试
for i in {1..10}; do curl -s http://localhost:8000/health & done | wait

# 测试API响应时间
time curl -s http://localhost:8000/ready | jq '.'
```

---

## 🔧 **故障排查命令**

### 当服务无响应时
```bash
# 1. 检查容器是否运行
docker ps | grep bookstore

# 2. 查看容器日志
docker logs bookstore-mysql
docker logs bookstore-redis
docker logs bookstore-qdrant

# 3. 检查网络连接
docker network ls
docker network inspect bookstore_bookstore-network

# 4. 重启服务
docker restart bookstore-mysql
docker restart bookstore-redis
docker restart bookstore-qdrant
```

### 当缓存问题时
```bash
# 清空Redis
docker exec bookstore-redis redis-cli FLUSHDB

# 重启Redis
docker restart bookstore-redis

# 检查Redis内存
docker exec bookstore-redis redis-cli INFO memory | grep used_memory_human
```

### 当数据库连接错误时
```bash
# 检查MySQL状态
docker exec bookstore-mysql mysql -u root -e "SELECT 1;"

# 查看MySQL错误日志
docker logs bookstore-mysql --tail=50

# 重启MySQL
docker restart bookstore-mysql
```

---

## 🌐 **在线仪表板**

| 工具 | URL | 用途 |
|------|-----|------|
| **Swagger UI** | http://localhost:8000/docs | 交互式API测试 |
| **ReDoc** | http://localhost:8000/redoc | API文档查看 |
| **Prometheus** | http://localhost:8000/metrics | 指标数据 |
| **Qdrant Web** | http://localhost:6333/dashboard | 向量数据库管理 |

---

## 💡 **常用组合命令**

### 快速诊断脚本
```bash
#!/bin/bash
echo "=== 📋 系统诊断报告 ===" 
echo "时间: $(date)"
echo ""
echo "1️⃣ 容器状态:"
docker ps --format "{{.Names}}\t{{.Status}}" | grep bookstore
echo ""
echo "2️⃣ 后端服务:"
curl -s http://localhost:8000/health
echo ""
echo "3️⃣ 数据库:"
docker exec bookstore-mysql mysql -u root bookstore -e "SELECT COUNT(*) as tables FROM information_schema.TABLES WHERE table_schema='bookstore';" 2>/dev/null | tail -1
echo ""
echo "4️⃣ 缓存大小:"
docker exec bookstore-redis redis-cli DBSIZE | grep keys
echo ""
echo "5️⃣ 向量DB:"
curl -s http://localhost:6333/collections | jq '.result.collections | length'
```

保存为 `diagnose.sh`，然后运行：
```bash
chmod +x diagnose.sh
./diagnose.sh
```

---

## 📞 需要帮助？

查看详细指南：`SERVICE_OBSERVATION_GUIDE.md`

所有命令都在此文件中有详细说明和示例。
