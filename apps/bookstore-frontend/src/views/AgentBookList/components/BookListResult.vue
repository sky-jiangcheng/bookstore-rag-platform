<template>
  <div class="book-list-result">
    <el-table :data="data.books" style="width: 100%" size="small">
      <el-table-column type="index" width="50" />
      <el-table-column prop="title" label="书名" min-width="200" show-overflow-tooltip />
      <el-table-column prop="author" label="作者" width="120" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column prop="price" label="价格" width="80">
        <template #default="{ row }">
          ¥{{ row.price.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="stock" label="库存" width="80">
        <template #default="{ row }">
          <el-tag :type="row.stock > 0 ? 'success' : 'danger'" size="small">
            {{ row.stock }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="relevance_score" label="相关度" width="100">
        <template #default="{ row }">
          <el-progress 
            :percentage="Math.round(row.relevance_score * 100)" 
            :color="getRelevanceColor(row.relevance_score)"
            :show-text="false"
            :stroke-width="8"
          />
          <span class="relevance-text">{{ Math.round(row.relevance_score * 100) }}%</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 统计信息 -->
    <div class="booklist-stats">
      <el-descriptions :column="3" size="small" border>
        <el-descriptions-item label="书籍数量">
          {{ data.books?.length || 0 }} 本
        </el-descriptions-item>
        <el-descriptions-item label="总价">
          ¥{{ data.total_price?.toFixed(2) || '0.00' }}
        </el-descriptions-item>
        <el-descriptions-item label="质量评分">
          <el-tag :type="getQualityType(data.quality_score)" effect="dark">
            {{ Math.round((data.quality_score || 0) * 100) }}%
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="置信度" :span="3">
          <el-progress 
            :percentage="Math.round((data.confidence || 0) * 100)" 
            :color="getConfidenceColor"
          />
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 分类分布 -->
    <div v-if="data.category_distribution" class="category-distribution">
      <h4>分类分布</h4>
      <div class="category-chips">
        <el-tag 
          v-for="(count, category) in data.category_distribution" 
          :key="category"
          class="category-tag"
          :type="getCategoryType(count)"
          effect="plain"
        >
          {{ category }}: {{ count }}本
        </el-tag>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button type="primary" @click="exportBookList">
        <el-icon><Download /></el-icon>
        导出书单
      </el-button>
      <el-button @click="regenerate">
        <el-icon><Refresh /></el-icon>
        重新生成
      </el-button>
      <el-button type="success" @click="saveBookList">
        <el-icon><Check /></el-icon>
        保存书单
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Download, Refresh, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { exportBookListToExcel } from '@/utils/booklistExport'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({
      books: [],
      total_price: 0,
      quality_score: 0,
      confidence: 0,
      category_distribution: {}
    })
  }
})

const emit = defineEmits(['regenerate', 'save'])

// 相关度颜色
const getRelevanceColor = (score) => {
  if (score >= 0.8) return '#67C23A'
  if (score >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

// 质量标签类型
const getQualityType = (score) => {
  if (!score) return 'info'
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'danger'
}

// 置信度颜色
const getConfidenceColor = computed(() => {
  const confidence = props.data.confidence || 0
  if (confidence >= 0.8) return '#67C23A'
  if (confidence >= 0.6) return '#E6A23C'
  return '#F56C6C'
})

// 分类标签类型
const getCategoryType = (count) => {
  if (count >= 5) return 'success'
  if (count >= 3) return 'warning'
  return 'info'
}

// 导出书单
const exportBookList = () => {
  try {
    exportBookListToExcel(props.data, {
      booklistName: props.data?.name || '书单'
    })
    ElMessage.success('书单已导出为 Excel')
  } catch (error) {
    console.error('Export booklist failed:', error)
    ElMessage.error(error.message || '导出失败')
  }
}

// 重新生成
const regenerate = () => {
  emit('regenerate')
}

// 保存书单
const saveBookList = () => {
  emit('save', props.data)
  ElMessage.success('书单已保存')
}
</script>

<style scoped>
.book-list-result {
  margin-top: 16px;
}

.relevance-text {
  font-size: 12px;
  color: #606266;
  margin-left: 8px;
}

.booklist-stats {
  margin-top: 16px;
}

.category-distribution {
  margin-top: 16px;
}

.category-distribution h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.category-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-tag {
  font-size: 12px;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
