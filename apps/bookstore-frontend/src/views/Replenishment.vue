<template>
  <div class="replenishment-container">
    <h2>补货推荐</h2>
    <el-card>
      <div class="toolbar">
        <el-button type="primary" @click="generatePlans">生成采购单</el-button>
        <el-button @click="refreshPlans">刷新缓存</el-button>
        <el-button @click="exportCSV">导出CSV</el-button>
      </div>
    </el-card>

    <el-card v-if="loading" style="margin-top: 20px;">
      <el-skeleton :rows="10" animated />
    </el-card>

    <el-card v-else-if="plans.length > 0" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>补货计划</span>
          <el-select v-model="filterStatus" placeholder="按状态筛选" style="width: 150px;">
            <el-option label="全部" :value="''" />
            <el-option label="待处理" :value="'pending'" />
            <el-option label="紧急" :value="'urgent'" />
            <el-option label="已批准" :value="'approved'" />
            <el-option label="已拒绝" :value="'rejected'" />
          </el-select>
        </div>
      </template>
      <el-table :data="filteredPlans" style="width: 100%">
        <el-table-column prop="book_title" label="书名" min-width="200" />
        <el-table-column prop="suggest_qty" label="建议采购量" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="推荐理由" min-width="200" />
        <el-table-column prop="create_time" label="创建时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button v-if="scope.row.status !== 'approved'" type="primary" size="small" @click="approvePlan(scope.row)">批准</el-button>
            <el-button size="small" @click="viewDetails(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-empty v-else style="margin-top: 40px;" description="暂无补货计划" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import request from '../utils/request'
import { ElMessage } from 'element-plus'

const plans = ref([])
const loading = ref(false)
const filterStatus = ref('')

const filteredPlans = computed(() => {
  if (!filterStatus.value) {
    return plans.value
  }
  return plans.value.filter(plan => plan.status === filterStatus.value)
})

const getPlans = async () => {
  loading.value = true
  try {
    const response = await request.get('/replenishment/plans', {
      params: { status: filterStatus.value || undefined }
    })
    plans.value = response.data.items || []
  } catch (error) {
    console.error('Get plans failed:', error)
    plans.value = []
  } finally {
    loading.value = false
  }
}

const generatePlans = async () => {
  try {
    await request.post('/replenishment/generate')
    ElMessage.success('采购单生成成功')
    await getPlans()
  } catch (error) {
    console.error('Generate plans failed:', error)
  }
}

const refreshPlans = async () => {
  loading.value = true
  try {
    await request.post('/replenishment/refresh')
    ElMessage.success('缓存刷新成功')
    await getPlans()
  } catch (error) {
    console.error('Refresh cache failed:', error)
    ElMessage.error('缓存刷新失败')
  } finally {
    loading.value = false
  }
}

const exportCSV = async () => {
  try {
    const response = await request.get('/replenishment/export', {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'replenishment_plans.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('CSV导出成功')
  } catch (error) {
    console.error('Export CSV failed:', error)
    ElMessage.error('CSV导出失败')
  }
}

const approvePlan = async (plan) => {
  try {
    console.log('Approving plan:', plan)
    console.log('Plan ID:', plan.id)
    
    if (!plan || !plan.id) {
      console.error('Invalid plan object or missing ID:', plan)
      ElMessage.error('计划信息无效')
      return
    }
    
    console.log('Sending approval request for plan ID:', plan.id)
    
    const response = await request.post(`/replenishment/approve/${plan.id}`, {
      reason: '手动批准'
    })
    
    console.log('Approval response:', response)
    ElMessage.success('计划已批准，可前往采购管理页面创建采购单')
    await getPlans()
  } catch (error) {
    console.error('Approve plan failed:', error)
    console.error('Error details:', error.response || error.message || error)
    ElMessage.error('批准失败，请重试')
  }
}

const viewDetails = (plan) => {
  // 查看详情逻辑
  ElMessage.info(`查看详情：${plan.book_title}`)
}

const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    urgent: 'danger',
    approved: 'success',
    rejected: 'warning'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    pending: '待处理',
    urgent: '紧急',
    approved: '已批准',
    rejected: '已拒绝'
  }
  return textMap[status] || status
}

onMounted(() => {
  getPlans()
})
</script>

<style scoped>
.replenishment-container {
  padding: 20px;
}

.toolbar {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>