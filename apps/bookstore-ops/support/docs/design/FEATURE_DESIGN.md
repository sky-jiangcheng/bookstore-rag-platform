# 需求解析与书单生成功能设计文档

## 1. 功能概述

本设计将智能推荐和书单推荐功能拆分为两个独立的菜单：

1. **需求解析**：使用对话窗口形式进行多轮对话，理解用户需求，生成提示词模板
2. **书单生成**：根据用户提供的提示词生成真正的书单，支持提示词检查和两种生成模式

## 2. 需求解析功能

### 2.1 核心功能

- **对话式交互**：使用Gemini大模型进行多轮对话，理解用户需求
- **用户画像收集**：职业、年龄段、领域范围、阅读偏好等
- **屏蔽词类别确定**：选择现有屏蔽类别或创建新类别
- **书单分类定义**：按军事、历史、传记、教辅等分类，并设置比例
- **限制条件设置**：比例误差范围、书单总数等
- **提示词模板生成**：生成规范的提示词模板
- **模板编码**：使用UUID作为唯一标识

### 2.2 技术实现

- **后端API**：`/api/v1/demand-analysis/dialogue` - 对话式需求解析
- **数据库模型**：
  - `DemandAnalysisSession` - 存储对话历史和当前状态
  - `PromptTemplate` - 存储生成的提示词模板
- **前端界面**：`/demand-analysis` - 对话式需求解析页面

### 2.3 工作流程

1. 用户进入需求解析页面，开始对话
2. 系统使用Gemini大模型进行多轮对话，收集信息
3. 系统实时更新需求状态，显示当前收集的信息
4. 用户确认需求后，系统生成提示词模板
5. 系统为模板生成UUID作为唯一标识
6. 用户可以复制模板ID或直接前往书单生成页面

## 3. 书单生成功能

### 3.1 核心功能

- **提示词输入**：支持直接输入提示词或选择现有模板
- **提示词检查**：验证提示词是否包含所有必要维度
- **两种生成模式**：
  - **精准生成**：检查提示词维度，缺失则弹出告警
  - **立即生成**：LLM自动补全提示词，直接生成书单
- **书单生成**：使用提示词匹配RAG数据库，加上后续计算进行裁剪
- **结果展示**：分类分布、书籍列表、匹配度等

### 3.2 技术实现

- **后端API**：
  - `/api/v1/book-list/validate-prompt` - 验证提示词
  - `/api/v1/book-list/generate` - 生成书单
- **前端界面**：`/book-list-generation` - 书单生成页面

### 3.3 工作流程

1. 用户进入书单生成页面，输入提示词或选择模板
2. 用户选择生成模式（精准生成或立即生成）
3. 系统验证提示词（精准模式）或自动补全（立即模式）
4. 系统使用RAG数据库匹配相关书籍
5. 系统根据提示词中的限制条件进行裁剪和排序
6. 系统展示生成的书单，包括分类分布和详细信息
7. 用户可以分享或导出书单

## 4. 技术架构

### 4.1 后端架构

- **FastAPI**：后端API框架
- **SQLAlchemy**：数据库ORM
- **MySQL**：存储结构化数据
- **Qdrant**：向量数据库，用于RAG检索
- **Gemini**：对话式需求解析
- **RAGService**：检索增强生成服务

### 4.2 前端架构

- **Vue3**：前端框架
- **Element Plus**：UI组件库
- **Vite**：构建工具
- **Vue Router**：路由管理

### 4.3 数据流

1. **需求解析流**：
   - 用户输入 → Gemini理解 → 收集信息 → 生成模板 → 存储模板

2. **书单生成流**：
   - 提示词输入 → 验证/补全 → RAG检索 → 计算裁剪 → 生成书单

## 5. 数据模型

### 5.1 DemandAnalysisSession

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | Integer | 主键 |
| session_id | String(36) | 会话ID (UUID) |
| user_id | Integer | 用户ID |
| dialogue_history | JSON | 对话历史 |
| current_context | JSON | 当前需求状态 |
| status | String(20) | 状态 (in_progress, completed, cancelled) |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 5.2 PromptTemplate

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | Integer | 主键 |
| template_id | String(36) | 模板ID (UUID) |
| user_id | Integer | 用户ID |
| template_content | JSON | 模板内容 |
| status | String(20) | 状态 (active, inactive) |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 6. API端点

### 6.1 需求解析API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/demand-analysis/dialogue` | POST | 对话式需求解析 |
| `/api/v1/demand-analysis/generate-template` | POST | 生成提示词模板 |
| `/api/v1/demand-analysis/session/{session_id}` | GET | 获取会话信息 |
| `/api/v1/demand-analysis/templates` | GET | 获取用户模板列表 |

### 6.2 书单生成API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/book-list/validate-prompt` | POST | 验证提示词 |
| `/api/v1/book-list/generate` | POST | 生成书单 |
| `/api/v1/book-list/history` | GET | 获取历史书单 |

## 7. 前端路由

| 路由 | 组件 | 功能 |
|------|------|------|
| `/demand-analysis` | `DemandAnalysis.vue` | 需求解析页面 |
| `/book-list-generation` | `BookListGeneration.vue` | 书单生成页面 |

## 8. 菜单配置

在前端菜单中添加以下项目：

- **智能服务** → **需求解析**：对话式需求解析入口
- **智能服务** → **书单生成**：书单生成入口

## 9. 提示词模板格式

```json
{
  "template_id": "uuid-string",
  "created_at": "2024-01-01T00:00:00Z",
  "user_profile": {
    "occupation": "职业",
    "age_group": "年龄段",
    "domain_scope": "领域范围",
    "reading_preferences": ["偏好1", "偏好2"]
  },
  "filter_category": {
    "category_name": "屏蔽词类别",
    "needs_new_category": false,
    "new_category_name": "新类别名称"
  },
  "book_categories": [
    {"category": "军事", "percentage": 30, "count": 6},
    {"category": "历史", "percentage": 30, "count": 6},
    {"category": "传记", "percentage": 40, "count": 8}
  ],
  "constraints": {
    "proportion_error_range": 5.0,
    "total_book_count": 20,
    "other_constraints": ["其他限制条件"]
  },
  "prompt": "请根据以下需求生成一份书单：\n\n用户画像：\n- 职业：..."
}
```

## 10. 技术亮点

- **对话式交互**：使用Gemini大模型进行多轮对话，提升用户体验
- **智能提示词生成**：自动生成规范的提示词模板
- **双重生成模式**：满足不同用户的需求，平衡效率和准确性
- **RAG检索优化**：使用专业向量数据库，提升检索性能
- **模块化设计**：功能拆分为独立模块，便于维护和扩展
- **完整的工作流**：从需求解析到书单生成的完整流程

## 11. 生产环境部署注意事项

- **大模型配置**：确保Gemini API密钥正确配置，考虑添加国产大模型作为备用
- **向量数据库**：生产环境建议使用Qdrant服务，而非内存存储
- **性能优化**：
  - 缓存热门提示词模板
  - 优化RAG检索参数
  - 考虑使用异步任务处理大计算量操作
- **监控告警**：添加API调用频率监控，防止大模型API调用超限
- **安全配置**：确保所有API端点都有适当的认证和授权

## 12. 未来扩展方向

- **个性化推荐**：基于用户历史行为优化推荐结果
- **多语言支持**：支持英文等其他语言的需求解析
- **更多生成选项**：添加按价格、出版日期等筛选条件
- **社交分享**：支持将书单分享到社交媒体
- **A/B测试**：通过A/B测试优化提示词模板和生成算法

## 13. 总结

本设计通过将智能推荐功能拆分为需求解析和书单生成两个独立模块，实现了更清晰的用户体验和更高效的推荐流程。使用对话式交互收集用户需求，生成规范的提示词模板，然后通过两种生成模式满足不同用户的需求，最终使用RAG技术生成高质量的书单。

该设计不仅提升了用户体验，也提高了系统的可维护性和扩展性，为未来的功能扩展打下了良好的基础。