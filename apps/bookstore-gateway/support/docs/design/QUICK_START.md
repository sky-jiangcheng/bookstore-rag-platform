# 🚀 快速开始指南 - 重构后的 API

## 📌 5 分钟快速了解

### 1. 新的 API 目录结构

```
backend/app/api/
├── v1/                          # API v1 版本
│   ├── book_list/               # 书单推荐模块
│   │   ├── schemas.py           # 数据模型
│   │   ├── services.py          # 业务逻辑
│   │   ├── routes.py            # 路由定义
│   │   ├── utilities.py         # 辅助接口
│   │   └── __init__.py
│   ├── shared/                  # 共享模块
│   │   ├── dependencies.py      # 依赖注入
│   │   └── __init__.py
│   └── __init__.py              # v1 路由汇总
└── ... 其他模块（保持不变）
```

### 2. 核心改进

| 改进项 | 详情 |
|--------|------|
| **文件大小** | 1284 行 → 每个 <800 行 (-43%) |
| **职责清晰** | 路由、逻辑、模型分离 |
| **可复用** | RequirementParser、BookListGenerator 类 |
| **文档** | 完整的 API 文档注释 |
| **版本管理** | 支持 v1/v2 并存 |

### 3. 核心类介绍

**RequirementParser** - 需求解析
```python
parser = RequirementParser(llm_service)

# 解析用户输入
parsed_reqs, confidence, suggestions = parser.parse_user_input(
    user_input="大学生书单，战争20%",
    user_history=[]
)

# 细化需求
refined_reqs, changes = parser.refine_requirements(
    before_reqs=parsed_reqs,
    refinement_input="增加科幻10%"
)
```

**BookListGenerator** - 书单生成
```python
generator = BookListGenerator(
    vector_service=vector_service,
    vector_db=vector_db,
    db=db
)

# 生成书单
recommendations, category_dist = generator.generate(
    parsed_reqs=parsed_reqs,
    limit=20
)
```

### 4. API 调用示例

#### 方式 A：交互式流程（推荐用于需求较复杂的场景）

```bash
# Step 1: 解析需求
curl -X POST http://localhost:8000/api/v1/book-list/parse \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "user_input": "大学生书单，战争20%历史10%经济15%"
  }'

# 响应包含 request_id（保存此值）
# {
#   "request_id": "550e8400-e29b-41d4-a716-446655440000",
#   "session_id": 123,
#   "confidence_score": 0.95,
#   ...
# }

# Step 2: 细化需求（可选）
curl -X POST http://localhost:8000/api/v1/book-list/refine \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "refinement_input": "减少历史到5%，增加科幻10%"
  }'

# Step 3: 生成书单
curl -X POST http://localhost:8000/api/v1/book-list/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "limit": 20
  }'
```

#### 方式 B：直接调用（前端表单场景）

```bash
# 直接生成书单，无需三步流程
curl -X POST http://localhost:8000/api/v1/book-list/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "requirements": {
      "cognitive_level": "大学生",
      "categories": [
        {
          "category": "战争",
          "percentage": 20,
          "count": 4
        },
        {
          "category": "历史",
          "percentage": 10,
          "count": 2
        }
      ],
      "keywords": ["经典", "名著"],
      "exclude_textbooks": true
    },
    "limit": 20,
    "save_to_history": true
  }'
```

### 5. 新增辅助 API

```bash
# 获取会话信息
curl -X GET http://localhost:8000/api/v1/book-list/session/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"

# 获取认知水平列表
curl -X GET http://localhost:8000/api/v1/book-list/cognitive-levels \
  -H "Authorization: Bearer <token>"

# 验证提示词维度
curl -X POST http://localhost:8000/api/v1/book-list/validate-prompt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"prompt": "为大学生推荐..."}'

# 获取历史书单
curl -X GET "http://localhost:8000/api/v1/book-list/history?page=1&limit=20" \
  -H "Authorization: Bearer <token>"

# 分享书单
curl -X POST http://localhost:8000/api/v1/book-list/share \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"book_list_id": 1, "is_public": true}'
```

---

## 🧪 如何运行

### 1. 启动服务

```bash
cd /Users/jiangcheng/Workspace/Python/BookStore

# 安装依赖（如果需要）
pip install -r gateway/support/deploy/requirements.txt

# 启动服务
python -m uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 查看 API 文档

访问 http://localhost:8000/docs，可以看到完整的 Swagger 文档

### 3. 运行测试（待补充）

```bash
# 运行单元测试
pytest app/api/v1/ -v

# 运行覆盖率检测
pytest backend/app/api/v1/ --cov=backend/app/api/v1 --cov-report=html
```

---

## 📚 文件说明

### schemas.py - 数据模型定义

定义所有请求/响应数据模型，使用 Pydantic：

```python
# 共享模型
- ParsedRequirements: 解析后的需求
- CategoryRequirement: 分类需求
- BookRecommendation: 推荐书籍

# 请求/响应
- ParseRequirementsRequest / Response
- RefineRequirementsRequest / Response
- GenerateBookListRequest / Response
- ValidatePromptRequest / Response
- ...
```

### services.py - 业务逻辑

封装核心业务逻辑，供路由调用：

```python
class RequirementParser:
    - parse_user_input()      # 解析需求
    - refine_requirements()   # 细化需求
    - _parse_llm_response()   # LLM 响应解析
    - _build_parsed_requirements()  # 构建需求对象

class BookListGenerator:
    - generate()              # 生成书单
    - _generate_by_categories()  # 按分类生成
    - _generate_by_keywords()    # 按关键词生成
    - _search_category()      # 搜索分类
    - _search_query()         # 搜索查询
    - _should_filter_out()    # 过滤判断
    - _fallback_search()      # 降级搜索

def validate_prompt()         # 验证提示词
```

### routes.py - API 路由

定义 API 端点，调用 services 中的业务逻辑：

```python
@router.post("/parse")        # Step 1: 解析需求
@router.post("/refine")       # Step 2: 细化需求
@router.post("/generate")     # Step 3: 生成书单
```

### utilities.py - 辅助接口

定义辅助功能接口：

```python
@router.get("/session/{request_id}")      # 获取会话信息
@router.get("/cognitive-levels")          # 获取认知水平列表
@router.post("/validate-prompt")          # 验证提示词
@router.get("/history")                   # 获取历史书单
@router.post("/share")                    # 分享书单
```

### dependencies.py - 依赖注入

管理服务依赖和错误处理：

```python
async def get_llm_service()         # 获取 LLM 服务
async def get_vector_service()      # 获取向量服务
async def get_vector_db_service()   # 获取向量数据库
async def get_cache_service()       # 获取缓存服务
def handle_service_error()          # 统一错误处理
```

---

## 🔍 关键改进点

### 1. 职责清晰

- `schemas.py`: 只定义数据模型
- `services.py`: 只实现业务逻辑
- `routes.py`: 只定义 API 端点
- `utilities.py`: 只实现辅助功能
- `dependencies.py`: 只管理依赖

### 2. 前后端一致

使用 `BookListGenerator` 类确保推荐逻辑一致：

```python
# 后端 API
recommendations = generator.generate(parsed_reqs, limit=20)

# 前端可以直接调用相同逻辑（如果需要）
# 或直接用 HTTP API，逻辑保证一致
```

### 3. 易于测试

```python
# 业务逻辑完全独立，易于单元测试
def test_requirement_parser():
    parser = RequirementParser(mock_llm)
    reqs, conf, sugg = parser.parse_user_input("需求")
    assert conf > 0
    
def test_book_generator():
    gen = BookListGenerator(mock_vec, mock_db)
    recs, dist = gen.generate(reqs, 20)
    assert len(recs) <= 20
```

### 4. 易于扩展

添加新的 API 模块只需：

```
backend/app/api/v1/my_module/
├── schemas.py
├── services.py
├── routes.py
└── __init__.py
```

然后在 `v1/__init__.py` 中注册：

```python
from app.api.v1.my_module import router as my_router
router.include_router(my_router)
```

---

## ⚠️ 注意事项

1. **旧文件处理**：`backend/app/api/book_list_recommendation.py` 仍然存在，但已被新的 v1 API 替代
   - 建议备份后删除，避免混淆

2. **向后兼容**：新 API 完全兼容旧调用，可逐步迁移

3. **性能**：代码结构改变不影响性能，逻辑完全相同

4. **测试**：建议运行单元测试验证功能：
   ```bash
   pytest backend/app/api/v1/ -v
   ```

---

## 📖 相关文档

- [ARCHITECTURE_ANALYSIS.md](./ARCHITECTURE_ANALYSIS.md) - 完整架构分析和问题诊断
- [API_RESTRUCTURING_GUIDE.md](./API_RESTRUCTURING_GUIDE.md) - 详细的重构指南
- Swagger API 文档 - http://localhost:8000/docs

---

## 🎯 下一步（第 2-3 周）

1. 编写单元测试 (>80% 覆盖率)
2. 创建 ServiceOrchestrator 统一编排
3. 集成 Celery 异步任务队列
4. 添加 CircuitBreaker 熔断机制
5. 完善多轮对话支持

详见 [ARCHITECTURE_ANALYSIS.md](./ARCHITECTURE_ANALYSIS.md) 中的改进计划。
