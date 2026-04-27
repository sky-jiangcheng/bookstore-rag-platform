<template>
  <div class="recommendation-container">
    <h2>新单推荐</h2>
    <el-card>
      <div class="card-header">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="结果数量">
            <el-select v-model="filterForm.limit" style="width: 120px;">
              <el-option label="10" :value="10" />
              <el-option label="20" :value="20" />
              <el-option label="50" :value="50" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="getRecommendations">刷新推荐</el-button>
          </el-form-item>
        </el-form>
        <div v-if="purchaseItems.length > 0" class="purchase-actions">
          <span style="margin-right: 10px;">已选择 {{ purchaseItems.length }} 本书籍</span>
          <el-button type="success" @click="goToPurchase">
            <el-icon><ShoppingCart /></el-icon>
            前往采购
          </el-button>
          <el-button @click="clearPurchaseItems">清空</el-button>
        </div>
      </div>
    </el-card>

    <el-card v-if="loading" style="margin-top: 20px;">
      <el-skeleton :rows="8" animated />
    </el-card>

    <el-card v-else-if="recommendations.length > 0" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>推荐书籍</span>
        </div>
      </template>
      <el-table :data="recommendations" style="width: 100%">
        <el-table-column prop="book_id" label="ID" width="80" />
        <el-table-column prop="title" label="书名" min-width="200" />
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            ¥{{ scope.row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="discount" label="折扣" width="100">
          <template #default="scope">
            {{ Math.round(scope.row.discount * 100) }}%
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="recommendation_score" label="推荐指数" width="120">
          <template #default="scope">
            <el-progress :percentage="Math.round(scope.row.recommendation_score * 100)" :color="getScoreColor(scope.row.recommendation_score)" :stroke-width="10" />
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="简介" min-width="300">
          <template #default="scope">
            <el-popover placement="top" :width="600" trigger="hover">
              <template #reference>
                <span>{{ scope.row.summary ? (scope.row.summary.length > 100 ? scope.row.summary.substring(0, 100) + '...' : scope.row.summary) : '-' }}</span>
              </template>
              <pre>{{ scope.row.summary || '-' }}</pre>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="primary" size="small" @click="addToCart(scope.row)">加入采购</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-empty v-else style="margin-top: 40px;" description="暂无推荐" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { ElMessage } from 'element-plus'
import { ShoppingCart } from '@element-plus/icons-vue'

const router = useRouter()
const filterForm = reactive({
  limit: 20
})

const recommendations = ref([])
const loading = ref(false)
const purchaseItems = ref([])

const getRecommendations = async () => {
  loading.value = true
  try {
    const response = await request.get('/recommendation/new', {
      params: { limit: filterForm.limit }
    })
    recommendations.value = response.data
  } catch (error) {
    console.error('Get recommendations failed:', error)
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

const addToCart = (book) => {
  // 检查书籍是否已在采购列表中
  const existingItem = purchaseItems.value.find(item => item.book_id === book.book_id)
  if (existingItem) {
    ElMessage.warning('该书籍已在采购列表中')
    return
  }
  
  // 添加到采购列表
  purchaseItems.value.push({
    book_id: book.book_id || book.id,
    title: book.title,
    author: book.author,
    quantity: 1,
    unit_price: book.price || 0
  })
  
  ElMessage.success(`已加入采购：${book.title}`)
}

const goToPurchase = () => {
  // 存储采购物品到sessionStorage
  sessionStorage.setItem('purchaseItems', JSON.stringify(purchaseItems.value))
  
  // 跳转到采购页面
  router.push('/purchase')
}

const clearPurchaseItems = () => {
  purchaseItems.value = []
  sessionStorage.removeItem('purchaseItems')
  ElMessage.info('已清空采购列表')
}

onMounted(() => {
  getRecommendations()
})
</script>

<style scoped>
.recommendation-container {
  padding: 20px;
}

.filter-form {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.purchase-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .purchase-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>