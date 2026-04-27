# Word2Vec 模型评估报告

## 📊 评估概述

**评估时间**: 2026-02-08  
**模型路径**: `backend/models/word2vec.model`  
**模型大小**: 7.6 KB  
**向量维度**: 100 维  

---

## 🔍 当前使用现状

### 1. 使用场景

| 文件 | 用途 | 说明 |
|------|------|------|
| `import_management.py` | 数据导入时生成向量 | 导入书籍时计算embedding |
| `duplicate_management.py` | 查重搜索 | 基于向量的相似度查重 |
| `batch_search.py` | 批量搜索 | 批量查询向量搜索 |
| `async_import.py` | 异步导入 | 异步任务中生成向量 |

### 2. VectorService 调用链

```
get_vector(text)
    ├── 尝试阿里云百炼API (1024维) ❌
    ├── 尝试 Gemini API (1536维) ❌
    └── 后备: 本地 Word2Vec (100维) ✅
```

**优先级**: 阿里云 > Gemini > Word2Vec

---

## ❌ 存在的问题

### 1. 向量维度不匹配 ⚠️ **严重**

```
Word2Vec:     100维
阿里云:       1024维
Gemini:       1536维
Qdrant配置:   1536维
```

**后果**:
- 如果用 Word2Vec 生成的向量存入 Qdrant（1536维），会导致维度不匹配错误
- 如果 Qdrant 已配置为 1536 维，Word2Vec 的 100 维向量无法存入
- 即使能存入，混合使用不同维度的向量会导致搜索结果混乱

### 2. 模型质量不足 ⚠️ **严重**

- **模型大小**: 仅 7.6KB（非常小的模型）
- **训练数据**: 看起来是用简单的示例数据训练的
- **词汇量**: 有限，很多书籍标题的词不在词汇表中
- **语义理解**: Word2Vec 是词袋模型，无法理解句子语义和上下文

**对比**:
| 模型 | 类型 | 维度 | 语义理解 | 适用场景 |
|------|------|------|----------|----------|
| Word2Vec | 静态词向量 | 100 | ❌ 无 | 简单的词级别相似度 |
| Gemini Embedding | 上下文嵌入 | 1536 | ✅ 强 | 语义搜索、推荐 |
| OpenAI Ada | 上下文嵌入 | 1536 | ✅ 强 | 语义搜索、推荐 |

### 3. 代码逻辑问题

**当前代码** (`vector_service.py` 240-268):
```python
# 后备方案：使用本地 gensim 模型
if self.Word2Vec is None:
    return np.random.randn(self.dimension).astype(np.float32)

words = combined_text.split()
vectors = []
for word in words:
    if self.model and word in self.model.wv:
        vectors.append(self.model.wv[word])
```

**问题**:
1. 简单的空格分词，对中文效果不好
2. 如果词不在词汇表中，就跳过（丢失信息）
3. 使用平均向量，无法捕捉句子整体语义
4. 返回随机向量作为 fallback，这会导致错误的相似度计算

---

## ✅ 建议方案

### 方案 1: 完全移除 Word2Vec (推荐 ⭐)

**理由**:
1. Gemini API 已配置且可用
2. AgenticRAG 架构完全依赖 Gemini embeddings (1536维)
3. Word2Vec 的 100 维向量与新架构不兼容
4. 移除后代码更简洁，维护成本更低

**实施步骤**:
1. 删除 `models/word2vec.model` 文件
2. 更新 `VectorService` 移除 Word2Vec 后备逻辑
3. 如果 API 都不可用，返回错误而不是随机向量
4. 更新所有使用 `VectorService` 的地方

**代码修改示例**:
```python
# 新的 get_vector 方法
def get_vector(self, text: str, summary: str = None) -> np.ndarray:
    combined_text = text
    if summary:
        combined_text = f"{text} {summary}"
    
    # 1. 尝试阿里云
    embedding = self._try_aliyun(combined_text)
    if embedding is not None:
        return embedding
    
    # 2. 尝试 Gemini
    embedding = self._try_gemini(combined_text)
    if embedding is not None:
        return embedding
    
    # 3. 没有可用服务，抛出异常
    raise VectorServiceError(
        "No embedding service available. "
        "Please configure Gemini API or Aliyun API."
    )
```

### 方案 2: 保留作为离线 fallback (不推荐)

**适用场景**:
- 需要完全离线运行（无网络）
- 无法使用任何外部 API

**需要改进**:
1. 重新训练 Word2Vec 模型，使用真实的图书数据
2. 增加词汇量到至少 10万+ 词汇
3. 改进中文分词（使用 jieba 等）
4. 统一向量维度为 1536（通过线性变换或 PCA）

**成本**:
- 需要大量标注数据
- 训练成本高
- 效果仍远不如 Gemini

### 方案 3: 使用开源 Embedding 模型 (可选)

**替代方案**:
- `BGE-M3` (BAAI)：开源，支持中英双语，1024维
- `text2vec` (Chinese)：中文语义向量，768维
- `all-MiniLM-L6-v2`：英文，384维

**实施**:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-m3')
embedding = model.encode(text)
```

**问题**:
- 需要安装 `sentence-transformers`（较大的依赖）
- 需要 GPU 才能获得较好性能
- 仍然需要处理维度不匹配问题

---

## 🎯 推荐决策

### 结论: **完全移除 Word2Vec**

**理由**:
1. ✅ Gemini API 已配置且可用 (`GEMINI_API_KEY` 已设置)
2. ✅ AgenticRAG 架构完全基于 1536 维 Gemini embeddings
3. ❌ Word2Vec 100 维与架构不兼容
4. ❌ Word2Vec 质量差，会导致错误的搜索结果
5. ❌ 维护成本高，代码复杂

---

## 📝 实施清单

### 步骤 1: 移除模型文件
```bash
rm /Users/jiangcheng/Workspace/Python/BookStore/backend/models/word2vec.model
rm /Users/jiangcheng/Workspace/Python/BookStore/models/word2vec.model
```

### 步骤 2: 重构 VectorService

**文件**: `backend/app/services/vector_service.py`

**修改内容**:
1. 移除 `Word2Vec` 相关导入
2. 移除 `_load_model()` 方法
3. 简化 `get_vector()` 方法
4. 如果无可用服务，抛出异常而不是返回随机向量

### 步骤 3: 更新配置

**文件**: `backend/config/config.yml`

移除:
```yaml
word2vec:
  model_path: "models/word2vec.model"
```

### 步骤 4: 更新所有调用点

需要更新的文件:
- `import_management.py` - 移除 Word2Vec 路径参数
- `duplicate_management.py` - 移除 Word2Vec 路径参数
- `batch_search.py` - 移除 Word2Vec 路径参数
- `async_import.py` - 移除 Word2Vec 路径参数

### 步骤 5: 测试验证

1. ✅ 确认 Gemini API 调用正常
2. ✅ 确认向量生成正确 (1536维)
3. ✅ 确认 Qdrant 存储正常
4. ✅ 确认搜索结果准确

---

## 🎉 预期效果

| 指标 | 移除前 | 移除后 |
|------|--------|--------|
| 代码复杂度 | 高（多fallback） | 低（直接调用API） |
| 向量质量 | 差（Word2Vec） | 好（Gemini） |
| 维度一致性 | ❌ 不匹配 | ✅ 统一1536维 |
| 维护成本 | 高 | 低 |
| 搜索结果准确性 | 低 | 高 |

---

## ⚠️ 风险提示

1. **网络依赖**: 移除 Word2Vec 后，系统完全依赖外部 API（Gemini/阿里云）
   - **缓解**: 确保 API key 有效，添加重试机制

2. **API 成本**: Gemini API 有调用成本
   - **缓解**: 添加缓存层（已配置 AgentCache）

3. **离线场景**: 无法在无网络环境使用
   - **缓解**: 如需离线，考虑部署本地 Embedding 服务

---

## 💡 最终建议

**立即执行**: 移除 Word2Vec，完全使用 Gemini embeddings

**原因**:
1. 你已经有 `GEMINI_API_KEY` 且配置正确
2. AgenticRAG 架构完全依赖高质量的语义向量
3. Word2Vec 已经成为技术债务，拖慢系统

**如需保留离线能力，建议**:
- 部署本地 Embedding 服务（如 Ollama + nomic-embed-text）
- 而不是使用质量差的 Word2Vec

---

**评估完成。建议移除 Word2Vec，是否需要我执行移除操作？**
