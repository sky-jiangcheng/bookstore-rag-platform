<template>
  <div class="smart-recommendation-container">
    <h2>智能书单推荐</h2>
    
    <el-card>
      <template #header>
        <div class="card-header">
          <span>智能推荐助手</span>
          <div>
            <el-tooltip content="管理屏蔽词配置">
              <el-button type="info" @click="goToFilterConfig">
                <el-icon><Close /></el-icon>
                屏蔽配置
              </el-button>
            </el-tooltip>
            <el-tooltip content="输入您的阅读需求，系统会智能分析并推荐合适的书籍">
              <el-button circle>
                <el-icon><QuestionFilled /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>
      </template>
      
      <div class="input-section">
        <el-form :model="form">
          <el-form-item label="您的阅读需求">
            <el-input
              v-model="form.user_input"
              type="textarea"
              :rows="6"
              placeholder="请详细描述您的阅读需求，例如：我想学习Python编程，需要入门到进阶的完整学习路径，最好包含实战项目..."
            />
          </el-form-item>
          <el-form-item label="推荐数量">
            <el-select v-model="form.limit" style="width: 120px;">
              <el-option label="10" :value="10" />
              <el-option label="20" :value="20" />
              <el-option label="50" :value="50" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="getSmartRecommendation" :loading="loading">
              <el-icon><Search /></el-icon>
              智能推荐
            </el-button>
            <el-button @click="resetForm">清空</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card v-if="loading" style="margin-top: 20px;">
      <el-skeleton :rows="8" animated />
    </el-card>

    <el-card v-else-if="recommendations.length > 0" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>推荐结果</span>
          <span class="result-count">共 {{ recommendations.length }} 本书籍</span>
        </div>
      </template>
      
      <div v-if="parsedRequirements" class="requirements-section" style="margin-bottom: 20px;">
        <h4>需求分析</h4>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="关键词">
            <el-tag v-for="keyword in parsedRequirements.keywords" :key="keyword" size="small" style="margin-right: 5px;">
              {{ keyword }}
            </el-tag>
            <span v-if="parsedRequirements.keywords.length === 0">无</span>
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag v-for="category in parsedRequirements.categories" :key="category" size="small" type="success" style="margin-right: 5px;">
              {{ category }}
            </el-tag>
            <span v-if="parsedRequirements.categories.length === 0">无</span>
          </el-descriptions-item>
          <el-descriptions-item label="约束条件">
            <el-tag v-for="constraint in parsedRequirements.constraints" :key="constraint" size="small" type="warning" style="margin-right: 5px;">
              {{ constraint }}
            </el-tag>
            <span v-if="parsedRequirements.constraints.length === 0">无</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div v-if="recommendationReason" class="recommendation-reason-section" style="margin-bottom: 20px;">
        <h4>推荐理由</h4>
        <el-card type="borderless" :body-style="{ padding: '10px' }">
          <el-alert
            :title="recommendationReason"
            type="info"
            :closable="false"
            show-icon
          />
        </el-card>
      </div>
      
      <el-table :data="recommendations" style="width: 100%">
        <el-table-column prop="book_id" label="ID" width="80" />
        <el-table-column prop="title" label="书名" min-width="200" />
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="publisher" label="出版社" width="150" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            ¥{{ scope.row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="score" label="匹配度" width="120">
          <template #default="scope">
            <el-progress :percentage="Math.round(scope.row.score * 100)" :color="getScoreColor(scope.row.score)" :stroke-width="10" />
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="100">
          <template #default="scope">
            <el-tag :type="getSourceType(scope.row.source)" size="small">
              {{ getSourceText(scope.row.source) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="primary" size="small" @click="addToCart(scope.row)">
              <el-icon><ShoppingCart /></el-icon>
              加入采购
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-else-if="form.user_input" style="margin-top: 20px;">
      <div class="no-results">
        <el-empty description="暂无推荐结果" />
        <p style="text-align: center; margin-top: 20px; color: #999;">
          请尝试调整您的需求描述，或者检查书库中是否有相关书籍
        </p>
      </div>
    </el-card>

    <el-empty v-else style="margin-top: 40px;" description="请输入您的阅读需求" />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { ElMessage } from 'element-plus'
import { Search, ShoppingCart, QuestionFilled, Close } from '@element-plus/icons-vue'

const router = useRouter()
const form = reactive({
  user_input: '',
  limit: 20
})

const recommendations = ref([])
const parsedRequirements = ref(null)
const recommendationReason = ref('')
const loading = ref(false)

const getSmartRecommendation = async () => {
  if (!form.user_input.trim()) {
    ElMessage.warning('请输入您的阅读需求')
    return
  }

  loading.value = true
  try {
    const response = await request.post('/smart/recommendation', {
      user_input: form.user_input,
      limit: form.limit
    })
    
    recommendations.value = response.data.recommendations || []
    parsedRequirements.value = response.data.parsed_requirements || null
    recommendationReason.value = response.data.recommendation_reason || ''
    
    if (recommendations.value.length === 0) {
      ElMessage.info('未找到匹配的书籍，请尝试调整您的需求描述')
    }
  } catch (error) {
    console.error('Get smart recommendation failed:', error)
    ElMessage.error('获取推荐失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const getScoreColor = (score) => {
  if (score > 0.8) return '#67c23a'
  if (score > 0.6) return '#409eff'
  if (score > 0.4) return '#e6a23c'
  return '#f56c6c'
}

const getSourceType = (source) => {
  switch (source) {
    case 'database': return 'primary'
    case 'vector': return 'info'
    case 'popular': return 'warning'
    default: return 'default'
  }
}

const getSourceText = (source) => {
  switch (source) {
    case 'database': return '数据库'
    case 'vector': return '向量搜索'
    case 'popular': return '热门推荐'
    default: return '其他'
  }
}

const resetForm = () => {
  form.user_input = ''
  form.limit = 20
  recommendations.value = []
  parsedRequirements.value = null
  recommendationReason.value = ''
}

const goToFilterConfig = () => {
  router.push('/filters')
}

const addToCart = (book) => {
  // 获取现有的采购列表
  const existingItems = JSON.parse(sessionStorage.getItem('purchaseItems') || '[]')
  
  // 检查书籍是否已在采购列表中
  const existingItem = existingItems.find(item => item.book_id === book.book_id)
  if (existingItem) {
    ElMessage.warning('该书籍已在采购列表中')
    return
  }
  
  // 添加到采购列表
  existingItems.push({
    book_id: book.book_id || book.id,
    title: book.title,
    author: book.author,
    quantity: 1,
    unit_price: book.price || 0
  })
  
  // 保存到sessionStorage
  sessionStorage.setItem('purchaseItems', JSON.stringify(existingItems))
  
  ElMessage.success(`已加入采购：${book.title}`)
}
</script>

<style scoped>
.smart-recommendation-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-section {
  margin-top: 20px;
}

.result-count {
  font-size: 14px;
  color: #999;
}

.requirements-section {
  background-color: #f9f9f9;
  padding: 15px;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .smart-recommendation-container {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>