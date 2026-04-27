<template>
  <el-card class="step-card">
    <template #header>
      <div class="card-header">
        <span><el-icon><CircleCheck /></el-icon> 步骤3：书单生成</span>
      </div>
    </template>

    <el-result
      icon="success"
      title="书单生成成功"
      sub-title="您的书单已成功生成，您可以分享给他人或直接用于采购"
    >
      <template #extra>
        <el-space wrap>
          <el-button type="primary" @click="handleShare">
            <el-icon><Share /></el-icon>
            分享书单
          </el-button>
          <el-button type="success" @click="handleAddToPurchase">
            <el-icon><ShoppingCart /></el-icon>
            加入采购
          </el-button>
          <el-button @click="handleCreateNew">
            <el-icon><Plus /></el-icon>
            创建新书单
          </el-button>
        </el-space>
      </template>
    </el-result>

    <el-card class="final-book-list">
      <template #header>
        <div class="card-header">
          <span>{{ store.advancedForm.name }}</span>
          <el-tag type="success">{{ store.selectedBooks.length }} 本书</el-tag>
        </div>
      </template>

      <el-descriptions :column="4" border>
        <el-descriptions-item label="总价格">
          <span style="font-size: 18px; color: #f56c6c; font-weight: bold;">
            ¥{{ store.selectedTotalPrice.toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="平均价格">
          ¥{{ averagePrice.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item label="预算使用">
          <el-progress
            :percentage="budgetPercentage"
            :color="store.budgetProgressColor"
          />
        </el-descriptions-item>
        <el-descriptions-item label="平均匹配度">
          {{ (store.averageScore * 100).toFixed(1) }}%
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <el-table :data="store.selectedBooks" style="width: 100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="title" label="书名" min-width="200" />
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            ¥{{ scope.row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="score" label="匹配度" width="120">
          <template #default="scope">
            <el-progress :percentage="Math.round(scope.row.score * 100)" :color="getScoreColor(scope.row.score)" />
          </template>
        </el-table-column>
        <el-table-column label="备注" width="150">
          <template #default="scope">
            <el-input v-model="scope.row.remark" placeholder="添加备注" size="small" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="satisfaction-card">
      <template #header>
        <span>满意度评分</span>
      </template>
      <el-form :model="store.feedback" label-width="100px">
        <el-form-item label="总体评分">
          <el-rate v-model="store.feedback.overall_score" allow-half show-text />
        </el-form-item>
        <el-form-item label="推荐准确性">
          <el-rate v-model="store.feedback.accuracy_score" allow-half />
        </el-form-item>
        <el-form-item label="价格合理性">
          <el-rate v-model="store.feedback.price_score" allow-half />
        </el-form-item>
        <el-form-item label="改进建议">
          <el-input
            v-model="store.feedback.suggestions"
            type="textarea"
            :rows="3"
            placeholder="请提出您的改进建议..."
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmitFeedback">提交反馈</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { CircleCheck, Share, ShoppingCart, Plus } from '@element-plus/icons-vue'
import { useRecommendationStore } from '@/stores/recommendation'
import { getScoreColor } from '@/utils/recommendation'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

const store = useRecommendationStore()
const router = useRouter()

const averagePrice = computed(() => {
  if (!store.selectedBooks.length) return 0
  return store.selectedTotalPrice / store.selectedBooks.length
})

const budgetPercentage = computed(() => {
  if (!store.advancedForm.budget) return 0
  return Math.round((store.selectedTotalPrice / store.advancedForm.budget) * 100)
})

const handleShare = () => {
  store.generateShareLink()
}

const handleAddToPurchase = async () => {
  try {
    const purchaseItems = store.selectedBooks.map(book => ({
      book_id: book.book_id,
      title: book.title,
      author: book.author,
      quantity: 1,
      unit_price: book.price,
      remark: book.remark
    }))

    sessionStorage.setItem('purchaseItems', JSON.stringify(purchaseItems))
    ElMessage.success(`已将 ${purchaseItems.length} 本书籍加入采购列表`)

    await ElMessageBox.confirm('书单已加入采购，是否前往采购页面？', '提示', {
      confirmButtonText: '前往采购',
      cancelButtonText: '留在当前页面',
      type: 'success'
    })

    router.push('/purchase')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Add to purchase failed:', error)
    }
  }
}

const handleCreateNew = () => {
  store.createNewBookList()
}

const handleSubmitFeedback = async () => {
  const result = await store.submitFeedback()
  if (result.success) {
    ElMessage.success('感谢您的反馈！')
  } else {
    ElMessage.error(result.message)
  }
}
</script>

<style scoped>
.step-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.final-book-list {
  margin-top: 20px;
}

.satisfaction-card {
  margin-top: 20px;
}
</style>
