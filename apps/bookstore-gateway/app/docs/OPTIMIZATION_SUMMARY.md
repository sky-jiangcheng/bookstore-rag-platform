# 需求分析优化总结

## 优化内容

### 1. 硬约束说明与增强

**原有问题**：硬约束定义不够明确，验证逻辑不完善

**优化方案**：
- 在 `Constraints` 类中为每个字段添加详细注释，说明硬约束的含义
- 新增预算、语言偏好、出版年份范围等约束字段
- 实现 `validate_constraints()` 函数进行约束有效性验证
- 使用 Pydantic 的 `Field` 约束进行基础验证（范围、类型等）

**文件**：[demand_analysis.py:36-54](bookstore-local-platform/apps/bookstore-gateway/app/api/demand_analysis.py#L36-L54)

**硬约束字段**：
```python
- proportion_error_range: 比例误差范围 (0-20%)
- total_book_count: 书单总数 (5-100本)
- budget: 预算上限 (可选)
- exclude_textbooks: 是否排除教材
- language_preference: 语言偏好 (cn/en/mixed)
- publish_year_range: 出版年份范围
- other_constraints: 其他限制条件
```

### 2. 通用文案处理

**原有问题**：
- 使用"通用"、"综合"等无意义的兜底文案
- 无法识别用户意图时仍然返回无效分类

**优化方案**：
- 移除所有通用兜底逻辑
- 当置信度低于阈值时，强制要求用户澄清
- 提供针对性的澄清引导，而非笼统提问
- 在模糊输入时返回空的分类列表，而非"综合"分类

**文件**：[requirement_agent.py:175-225](bookstore-local-platform/apps/bookstore-gateway/app/agents/requirement_agent.py#L175-L225)

**改进效果**：
```
输入："推荐几本书"
- 优化前：返回 [{"name": "综合", "percentage": 100}]
- 优化后：返回 [] + 澄清问题
```

### 3. 关键词优化

**原有问题**：
- 仅支持"大学生"等少数职业关键词
- 年龄段、阅读水平识别不完善
- 书籍分类覆盖不全

**优化方案**：
- 创建扩展的关键词配置文件 [keywords_config.py](bookstore-local-platform/apps/bookstore-gateway/app/constants/keywords_config.py)
- 覆盖15+职业维度（程序员、教师、产品经理、设计师等）
- 4个年龄段（儿童、青少年、成人、老年人）
- 4个阅读水平（入门、进阶、高级、学术）
- 20+书籍分类主题
- 基于匹配度的动态置信度计算

**关键词覆盖示例**：
```python
# 职业维度
TARGET_AUDIENCE_OCCUPATION = {
    "程序员": ["程序员", "开发", "编程", "代码", "软件"],
    "产品经理": ["产品经理", "pm", "产品", "需求"],
    "设计师": ["设计师", "设计", "ui", "ux"],
    ...
}

# 年龄维度
TARGET_AUDIENCE_AGE = {
    "儿童": ["儿童", "小朋友", "小孩", "幼儿"],
    "青少年": ["青少年", "初中", "高中"],
    ...
}

# 阅读水平
READING_LEVEL = {
    "入门": ["入门", "基础", "新手", "零基础"],
    "进阶": ["进阶", "提升", "深入"],
    ...
}
```

### 4. 提示词模板优化

**原有问题**：
- 提示词模板缺乏针对性
- 引导语不够具体
- 未充分利用已有的需求信息

**优化方案**：
- 根据目标受众定制推荐策略
- 明确硬约束要求
- 提供具体的选书标准
- 生成可执行的生成指令

**文件**：[demand_analysis.py:145-177](bookstore-local-platform/apps/bookstore-gateway/app/api/demand_analysis.py#L145-L177)

**优化后的模板结构**：
```
# 图书推荐任务

## 目标受众
- 职业相关的选书策略

## 选书标准
1. 权威性
2. 时效性
3. 适用性
4. 职业定制标准

## 书单结构
- 分类1: 30% (6本)
- 分类2: 50% (10本)

## 硬约束（必须严格遵守）
1. 总数约束：必须正好 20 本
2. 比例约束：偏差不超过 ±5%
3. 预算约束
...
```

### 5. 对话提示优化

**原有问题**：
- 澄清问题过于笼统
- 未提供具体选项
- 重复提问已收集的信息

**优化方案**：
- 分析缺失信息，针对性提问
- 提供具体选项（如：程序员/教师/大学生）
- 一次聚焦1-2个关键信息
- 避免重复收集

**文件**：[demand_analysis.py:119-143](bookstore-local-platform/apps/bookstore-gateway/app/api/demand_analysis.py#L119-L143)

## 测试验证

### 测试用例覆盖

```
✓ 程序员识别：推荐一些编程书给开发者
✓ 大学生识别：本科生适合的算法书
✓ 产品经理识别：产品经理需要读什么书
✓ 儿童识别：给小孩子看的绘本
✓ 预算提取：预算800元的书籍推荐
✓ 模糊输入澄清：推荐几本书
```

### 硬约束验证

```
✓ 有效约束：正常通过
✓ 无效比例范围：Pydantic 正确拒绝
✓ 无效书籍总数：Pydantic 正确拒绝
✓ 负数预算：Pydantic 正确拒绝
✓ 无效语言偏好：正确拒绝
```

## 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/constants/keywords_config.py` | 新增 | 扩展关键词配置 |
| `app/agents/requirement_agent.py` | 修改 | 优化启发式分析逻辑 |
| `app/api/demand_analysis.py` | 修改 | 增强硬约束和提示词模板 |
| `app/tests/test_requirement_agent_optimized.py` | 新增 | 单元测试 |
| `app/tests/quick_test.py` | 新增 | 快速验证脚本 |

## 使用示例

```python
from app.agents.requirement_agent import RequirementAgent

agent = RequirementAgent()
result = await agent.analyze("程序员想学习人工智能和机器学习")

# 输出：
# {
#   "target_audience": {
#     "occupation": "程序员",
#     "age_group": "未识别",
#     "reading_level": "未识别"
#   },
#   "categories": [
#     {"name": "编程", "percentage": 25},
#     {"name": "人工智能", "percentage": 50},
#     {"name": "教育", "percentage": 25}
#   ],
#   "constraints": {"budget": null, ...},
#   "confidence": 0.6,
#   "needs_clarification": true,
#   "clarification_questions": ["请问读者的年龄段是？...", "请问读者的阅读水平是？..."]
# }
```

## 后续建议

1. 持续扩展关键词库，覆盖更多垂直领域
2. 引入用户反馈机制，动态调整置信度阈值
3. 考虑使用向量语义匹配，提升关键词识别准确度
4. 添加A/B测试，验证优化效果对用户满意度的影响
