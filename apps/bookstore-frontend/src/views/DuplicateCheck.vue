<template>
  <div class="duplicate-check-container">
    <h2>智能查重</h2>
    <el-card>
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="查询内容">
          <el-input v-model="searchForm.query" placeholder="请输入书名或条码" style="width: 300px;" />
        </el-form-item>
        <el-form-item label="结果数量">
          <el-select v-model="searchForm.limit" style="width: 120px;">
            <el-option label="10" :value="10" />
            <el-option label="20" :value="20" />
            <el-option label="50" :value="50" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="loading" style="margin-top: 20px;">
      <el-skeleton :rows="5" animated />
    </el-card>

    <!-- 告警提示 -->
    <el-alert
      v-if="warning"
      :title="warning"
      type="warning"
      show-icon
      style="margin-top: 20px;"
    />

    <!-- 结果标签页 -->
    <el-card v-if="!loading" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>查重结果</span>
        </div>
      </template>
      
      <el-alert
        type="info"
        title="相似度结果：数据库相似结果和向量相似度推荐已合并显示"
        show-icon
        style="margin-bottom: 20px;"
      />
      <el-table v-if="combinedResults.length > 0" :data="combinedResults" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="书名" min-width="200" />
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="barcode" label="条码" width="180" />
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.type === 'like' ? 'primary' : 'info'">
              {{ scope.row.type === 'like' ? '数据库相似' : '向量相似' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="相似度" width="100">
          <template #default="scope">
            <el-progress :percentage="Math.round(scope.row.score * 100)" :color="getScoreColor(scope.row.score)" :stroke-width="10" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="primary" size="small" @click="merge(scope.row)">合并</el-button>
            <el-button size="small" @click="ignore(scope.row)">忽略</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无结果" />
    </el-card>

    <el-empty v-if="!loading && combinedResults.length === 0" style="margin-top: 40px;" description="暂无结果" />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import request from '../utils/request'
import { ElMessage } from 'element-plus'

const searchForm = reactive({
  query: '',
  limit: 20
})

const likeResults = ref([])
const vectorResults = ref([])
const combinedResults = ref([])
const loading = ref(false)
const warning = ref('')

const search = async () => {
  if (!searchForm.query) {
    return
  }

  loading.value = true
  try {
    const response = await request.post('/duplicates/search', {
      query: searchForm.query,
      limit: searchForm.limit
    })
    
    // 处理新的响应结构
    likeResults.value = response.data.like_results || []
    vectorResults.value = response.data.vector_results || []
    warning.value = response.data.warning || ''
    
    // 合并结果
    combinedResults.value = [
      ...likeResults.value.map(item => ({ ...item, id: item.book_id, type: 'like' })),
      ...vectorResults.value.map(item => ({ ...item, id: item.book_id, type: 'vector' }))
    ].sort((a, b) => b.score - a.score)
  } catch (error) {
    console.error('Search failed:', error)
    ElMessage.error('搜索失败，请重试')
  } finally {
    loading.value = false
  }
}

const getScoreColor = (score) => {
  if (score > 0.9) return '#67c23a'
  if (score > 0.8) return '#e6a23c'
  return '#f56c6c'
}

const merge = async (row) => {
  try {
    // 合并到最匹配的记录（优先数据库相似结果，按相似度排序）
    const allResults = [...likeResults.value, ...vectorResults.value]
    if (allResults.length > 0) {
      // 过滤掉当前行，然后按相似度排序
      const candidateResults = allResults.filter(item => item.book_id !== row.book_id)
      if (candidateResults.length > 0) {
        // 按相似度排序，优先选择相似度高的
        candidateResults.sort((a, b) => b.score - a.score)
        const targetBook = candidateResults[0]
        
        const response = await request.post(`/duplicates/merge/${row.book_id}`, {
                  target_book_id: targetBook.book_id
                })
        ElMessage.success(`成功将《${row.title}》合并到《${targetBook.title}》`)
        // 重新搜索
        await search()
      } else {
        ElMessage.warning('没有可合并的目标书籍')
      }
    } else {
      ElMessage.warning('没有可合并的目标书籍')
    }
  } catch (error) {
    console.error('Merge failed:', error)
    ElMessage.error('合并失败，请重试')
  }
}

const ignore = async (row) => {
  try {
    await request.post(`/duplicates/ignore/${row.book_id}`)
    ElMessage.success(`成功忽略书籍：${row.title}`)
    // 从结果中移除
    likeResults.value = likeResults.value.filter(item => item.book_id !== row.book_id)
    vectorResults.value = vectorResults.value.filter(item => item.book_id !== row.book_id)
  } catch (error) {
    console.error('Ignore failed:', error)
    ElMessage.error('忽略失败，请重试')
  }
}
</script>

<style scoped>
.duplicate-check-container {
  padding: 20px;
}

.search-form {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>