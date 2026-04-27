<template>
  <div class="logs-container">
    <h2>日志管理</h2>
    
    <el-card>
      <template #header>
        <div class="card-header">
          <span>日志列表</span>
          <el-select v-model="logType" placeholder="选择日志类型" @change="handleLogTypeChange" style="width: 150px;">
            <el-option label="操作日志" value="operation" />
            <el-option label="批量操作日志" value="batch" />
          </el-select>
        </div>
      </template>
      
      <!-- 筛选表单 -->
      <el-form :inline="true" :model="logFilter" class="filter-form" style="margin-bottom: 20px;">
        <el-form-item label="操作类型">
          <el-select v-model="logFilter.operation_type" placeholder="请选择操作类型" clearable>
            <el-option label="导入" value="IMPORT_BOOKS" />
            <el-option label="合并" value="MERGE_BOOK" />
            <el-option label="忽略" value="IGNORE_BOOK" />
            <el-option label="刷新" value="REFRESH" />
            <el-option label="导出" value="EXPORT" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作状态">
          <el-select v-model="logFilter.status" placeholder="请选择操作状态" clearable>
            <el-option label="成功" value="SUCCESS" />
            <el-option label="失败" value="FAILURE" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="logFilter.start_time"
            type="date"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="logFilter.end_time"
            type="date"
            placeholder="选择结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="getLogs">查询</el-button>
          <el-button @click="resetLogFilter">重置</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 日志表格 -->
      <el-table
        v-loading="loading"
        :data="logData"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="operation_type" label="操作类型" width="120">
          <template #default="scope">
            <el-tag :type="getOperationTypeTagType(scope.row.operation_type)">
              {{ getOperationTypeLabel(scope.row.operation_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operation_status" label="操作状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.operation_status === 'SUCCESS' ? 'success' : 'danger'">
              {{ scope.row.operation_status === 'SUCCESS' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="logType === 'operation'" prop="target_id" label="目标ID" width="100" />
        <el-table-column v-if="logType === 'batch'" prop="total_count" label="总数量" width="100" />
        <el-table-column v-if="logType === 'batch'" prop="success_count" label="成功数量" width="100">
          <template #default="scope">
            <span class="success-count">{{ scope.row.success_count }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="logType === 'batch'" prop="failure_count" label="失败数量" width="100">
          <template #default="scope">
            <span class="failure-count">{{ scope.row.failure_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="操作描述" min-width="300">
          <template #default="scope">
            <el-popover placement="top" :width="400" trigger="hover">
              <template #reference>
                <span>{{ truncateDescription(scope.row.description) }}</span>
              </template>
              <pre>{{ scope.row.description }}</pre>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="200">
          <template #default="scope">
            <el-popover placement="top" :width="400" trigger="hover" v-if="scope.row.error_message">
              <template #reference>
                <span class="error-text">{{ truncateDescription(scope.row.error_message) }}</span>
              </template>
              <pre>{{ scope.row.error_message }}</pre>
            </el-popover>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="操作时间" width="180" />
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination" style="margin-top: 20px;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '../utils/request'
import { ElMessage } from 'element-plus'

// 日志类型
const logType = ref('operation')

// 日志数据
const logData = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const logFilter = reactive({
  operation_type: '',
  status: '',
  start_time: '',
  end_time: ''
})

// 获取日志
const getLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      operation_type: logFilter.operation_type || undefined,
      status: logFilter.status || undefined,
      start_time: logFilter.start_time || undefined,
      end_time: logFilter.end_time || undefined
    }
    
    const endpoint = `/logs/${logType.value}`
    const response = await request.get(endpoint, { params })
    logData.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

// 重置日志筛选
const resetLogFilter = () => {
  Object.assign(logFilter, {
    operation_type: '',
    status: '',
    start_time: '',
    end_time: ''
  })
  currentPage.value = 1
  getLogs()
}

// 处理分页大小变化
const handleSizeChange = (size) => {
  pageSize.value = size
  getLogs()
}

// 处理页码变化
const handleCurrentChange = (current) => {
  currentPage.value = current
  getLogs()
}

// 处理日志类型变化
const handleLogTypeChange = () => {
  currentPage.value = 1
  getLogs()
}

// 获取操作类型标签类型
const getOperationTypeTagType = (operationType) => {
  const typeMap = {
    'IMPORT_BOOKS': 'primary',
    'MERGE_BOOK': 'success',
    'IGNORE_BOOK': 'warning',
    'REFRESH': 'info',
    'EXPORT': 'danger'
  }
  return typeMap[operationType] || 'default'
}

// 获取操作类型标签
const getOperationTypeLabel = (operationType) => {
  const labelMap = {
    'IMPORT_BOOKS': '导入',
    'MERGE_BOOK': '合并',
    'IGNORE_BOOK': '忽略',
    'REFRESH': '刷新',
    'EXPORT': '导出'
  }
  return labelMap[operationType] || operationType
}

// 截断描述
const truncateDescription = (description) => {
  if (!description) return ''
  return description.length > 50 ? description.substring(0, 50) + '...' : description
}

// 初始化数据
onMounted(() => {
  getLogs()
})
</script>

<style scoped>
.logs-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}

.error-text {
  color: #f56c6c;
}

.success-count {
  color: #67c23a;
  font-weight: bold;
}

.failure-count {
  color: #f56c6c;
  font-weight: bold;
}

.el-table {
  width: 100%;
}
</style>