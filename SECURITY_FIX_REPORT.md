# BookStore 安全修复报告

**修复日期：** 2026-04-27  
**修复范围：** bookstore-local-platform/apps/（5个微服务）

---

## 修复概览

| 优先级 | 问题类型 | 受影响服务数 | 状态 |
|--------|----------|-------------|------|
| 🔴 P0 | 密码哈希从 SHA-256 迁移至 bcrypt | 4个 | ✅ 已修复 |
| 🔴 P0 | JWT 从自制 Token 迁移至 python-jose | 4个 | ✅ 已修复 |
| 🔴 P0 | 数据库连接泄漏（auth_service + permission_service） | 5个 | ✅ 已修复 |
| 🟠 P1 | 硬编码默认 JWT 密钥 + 运行时安全检查 | 7个 | ✅ 已修复 |
| 🟠 P1 | 降级认证绕过风险 | 全部 | ✅ 已修复 |
| 🟡 P2 | rag_service 测试数据混入生产响应 | rag | ✅ 已修复 |
| 🟡 P2 | docker-compose build context 路径失效 | 2个 | ✅ 已修复 |

---

## 详细修复说明

### P0-1：密码哈希算法升级（bcrypt）

**问题：** `bookstore-auth`、`bookstore-gateway`、`bookstore-catalog`、`bookstore-ops` 使用 `hashlib.sha256` 无盐哈希，极易受彩虹表攻击。

**修复：** 迁移至 `passlib.context.CryptContext(schemes=["bcrypt"])` 标准哈希。

**迁移兼容性：** `verify_password` 方法增加了 SHA-256 向后兼容逻辑，已有旧密码的用户仍可正常登录（迁移期间）：
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 优先尝试 bcrypt 验证
    try:
        if pwd_context.verify(plain_password, hashed_password):
            return True
    except Exception:
        pass
    # 兼容旧 SHA-256 哈希（迁移期间）
    import hashlib
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
```

**受影响文件：**
- `apps/bookstore-auth/app/services/auth_service.py`
- `apps/bookstore-gateway/app/services/auth_service.py`
- `apps/bookstore-catalog/app/services/auth_service.py`
- `apps/bookstore-ops/app/services/auth_service.py`
- `apps/bookstore-gateway/support/app/services/auth_service.py`
- `apps/bookstore-ops/support/app/services/auth_service.py`

---

### P0-2：JWT Token 标准化

**问题：** 4个服务使用自制 `JSON + SHA-256签名` 的 Token，不符合 RFC 7519 标准，缺乏算法标识、类型头等安全要素。

**修复：** 迁移至 `python-jose` 标准 JWT 实现：
```python
from jose import JWTError, jwt

# 创建 token
encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# 验证 token
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

⚠️ **注意：** 升级后所有旧格式 Token 将立即失效，需要重新登录。

---

### P0-3：数据库连接泄漏修复

**问题：** `auth_service.py` 和 `permission_service.py` 中共 42+ 处 `db = next(get_db())` 调用后未关闭连接，高并发时导致连接池耗尽。

**修复：** 所有手动获取的连接统一添加 `try/finally` 保证关闭：
```python
# ❌ 修复前
db = next(get_db())
user = db.query(User).filter(...).first()

# ✅ 修复后
db = None
try:
    db = next(get_db())
    user = db.query(User).filter(...).first()
    return user
finally:
    if db:
        db.close()
```

**受影响文件：**
- `apps/bookstore-*/app/services/auth_service.py`（各2处）
- `apps/bookstore-*/app/services/permission_service.py`（各4处）

---

### P1-1：JWT 密钥安全加固

**问题：** 7个 `config_loader.py` 中 `get_jwt_config()` 方法默认返回硬编码占位密钥 `"your-secret-key-here-change-in-production"`。

**修复：** 添加运行时安全检查：
- **生产/staging 环境：** 若无有效密钥则 `sys.exit(1)` 拒绝启动
- **开发/测试环境：** 自动生成 `secrets.token_urlsafe(32)` 临时密钥并打印警告

```python
if not current_key or current_key == placeholder:
    if env in ("production", "prod", "staging"):
        logger.error("JWT_SECRET_KEY 未配置，生产环境禁止启动！")
        sys.exit(1)
    else:
        config["secret_key"] = secrets.token_urlsafe(32)
        logger.warning("JWT_SECRET_KEY 未配置，已生成随机临时密钥...")
```

**配置方法：** 通过环境变量 `JWT_SECRET_KEY` 注入密钥：
```bash
export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
```

---

### P1-2：降级认证绕过加固

**问题：** `_degraded_auth_enabled()` 的判断逻辑未显式排除生产环境，存在配置错误时的绕过风险。

**修复：** 增加生产/预发布环境的强制禁用：
```python
def _degraded_auth_enabled() -> bool:
    app_env = os.getenv("APP_ENV", "development").lower()
    # 生产/预发布环境强制禁用（无论任何环境变量如何设置）
    if app_env in ("production", "prod", "staging"):
        return False
    flag = os.getenv("BOOKSTORE_DEGRADED_AUTH", "").lower() in {"1", "true", "yes"}
    enabled = app_env == "testing" or flag
    if enabled:
        logger.warning("⚠️ 降级认证已启用，请勿在生产环境使用！")
    return enabled
```

---

### P2-1：删除 rag_service 中的测试数据

**问题：** 当向量检索和数据库查询均无结果时，`rag_service.py` 会将硬编码的假书籍（"Python编程从入门到精通"、作者"张三"等）作为真实推荐返回给用户。

**修复：** 删除该兜底测试数据块，当无结果时返回空列表并正常告知用户。

---

### P2-2：docker-compose build context 路径修复

**问题：** `support/deploy/docker-compose.yml` 中所有服务的 `context` 路径指向不存在的 `../../../store-*` 目录。

**修复：** 更新为正确的相对路径 `../../bookstore-*`：
```yaml
# ❌ 修复前
context: ../../../store-gateway

# ✅ 修复后
context: ../../bookstore-gateway
```

---

## 未修复的已知问题（待处理）

### P2（建议后续处理）

1. **双重数据库引擎定义**
   - 问题：`config.py` 和 `database.py` 分别创建独立的 `engine` 和 `SessionLocal`
   - 影响：资源浪费，连接池配置可能不一致
   - 建议：统一在 `database.py` 中创建引擎，`config.py` 只做配置读取

2. **向量维度不一致**
   - 问题：`config_loader.py` 默认维度 100，但 Qdrant/embedding 模型实际使用 1536 维
   - 建议：确认 embedding 模型的实际维度并统一配置

### P3（长期改进）

3. **静默异常吞掉（391处）**
   - 问题：大量 `except Exception: return None` 导致错误无法追踪
   - 建议：改为 `logger.exception("...")` 后再返回

4. **密码迁移计划**
   - 当前 `verify_password` 临时兼容旧 SHA-256 哈希
   - 建议：在用户下次登录时自动将密码重新哈希为 bcrypt 格式
   - 完成迁移后删除 SHA-256 兼容逻辑

---

## 部署注意事项

1. **必须先配置** `JWT_SECRET_KEY` 环境变量再启动生产环境
2. 升级后所有用户需要**重新登录**（旧 Token 格式已变更）
3. 旧密码兼容模式在迁移期间有效，建议 30 天后关闭
4. docker-compose 路径已修正，但需确认各服务目录下存在有效的 `Dockerfile`

---

*报告由自动化安全扫描与修复流程生成*
