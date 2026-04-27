<template>
  <div class="filter-management-container">
    <el-card class="filter-card">
      <template #header>
        <div class="card-header">
          <span>屏蔽类别管理</span>
          <div class="category-header-actions">
            <el-input
              v-model="store.categorySearchQuery"
              placeholder="搜索类别名称"
              style="width: 250px; margin-right: 10px"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon class="el-input__icon"><Search /></el-icon>
              </template>
              <template #append>
                <el-button @click="handleSearch"><el-icon><Search /></el-icon></el-button>
              </template>
            </el-input>
            <el-button type="success" @click="store.openImportDialog">
              <el-icon><Upload /></el-icon>
              导入文档
            </el-button>
            <el-button type="primary" @click="store.openAddCategoryDialog">
              <el-icon><Plus /></el-icon>
              新增类别
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="store.filteredCategories" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="类别名称" min-width="150" />
        <el-table-column prop="description" label="类别描述" min-width="200" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button 
              size="small" 
              @click="handleViewKeywords(scope.row)"
              :disabled="!scope.row.is_active"
            >
              管理关键词
            </el-button>
            <el-button 
              size="small" 
              type="primary" 
              @click="store.openEditCategoryDialog(scope.row)"
            >
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="handleDeleteCategory(scope.row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页组件 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="store.currentPage"
          v-model:page-size="store.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="store.totalCategories"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
      
      <!-- 批量操作工具栏 -->
      <div class="batch-actions" v-if="selectedCategories.length > 0">
        <el-tag size="small" type="info">已选择 {{ selectedCategories.length }} 个类别</el-tag>
        <el-button size="small" @click="handleBatchDelete">批量删除</el-button>
        <el-button size="small" @click="handleBatchActivate">批量激活</el-button>
        <el-button size="small" @click="handleBatchDeactivate">批量停用</el-button>
        <el-button size="small" @click="selectedCategories = []">取消选择</el-button>
      </div>
    </el-card>
    
    <!-- 各类对话框组件 -->
    <keyword-dialog />
    <category-dialog />
    <batch-keyword-dialog />
    <import-dialog />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useFilterStore } from '@/stores/filter'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Search } from '@element-plus/icons-vue'

// 动态导入对话框组件
import KeywordDialog from './components/KeywordDialog.vue'
import CategoryDialog from './components/CategoryDialog.vue'
import BatchKeywordDialog from './components/BatchKeywordDialog.vue'
import ImportDialog from './components/ImportDialog.vue'

const store = useFilterStore()
const selectedCategories = ref([])

onMounted(() => {
  store.loadCategories()
})

const handleSearch = async () => {
  const result = await store.loadCategories()
  if (!result.success) ElMessage.error(result.message)
}

const handleViewKeywords = async (category) => {
  const result = await store.viewKeywords(category)
  if (!result.success) ElMessage.error(result.message)
}

const handleDeleteCategory = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该类别吗？', '提示', { type: 'warning' })
    const result = await store.deleteCategory(id)
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消
  }
}

const handleSelectionChange = (val) => {
  selectedCategories.value = val
}

const handleSizeChange = (size) => {
  store.pageSize = size
  store.loadCategories()
}

const handleCurrentChange = (current) => {
  store.currentPage = current
  store.loadCategories()
}

const handleBatchDelete = async () => {
  if (selectedCategories.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedCategories.value.length} 个类别吗？`, '提示', { type: 'warning' })
    const ids = selectedCategories.value.map(cat => cat.id)
    const result = await store.batchDeleteCategories(ids)
    if (result.success) {
      ElMessage.success(result.message)
      selectedCategories.value = []
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消
  }
}

const handleBatchActivate = async () => {
  if (selectedCategories.value.length === 0) return
  
  const ids = selectedCategories.value.map(cat => cat.id)
  const result = await store.batchUpdateCategoryStatus(ids, true)
  if (result.success) {
    ElMessage.success(result.message)
    selectedCategories.value = []
  } else {
    ElMessage.error(result.message)
  }
}

const handleBatchDeactivate = async () => {
  if (selectedCategories.value.length === 0) return
  
  const ids = selectedCategories.value.map(cat => cat.id)
  const result = await store.batchUpdateCategoryStatus(ids, false)
  if (result.success) {
    ElMessage.success(result.message)
    selectedCategories.value = []
  } else {
    ElMessage.error(result.message)
  }
}
</script>

<style scoped>
.filter-management-container {
  padding: 20px;
}

.category-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.batch-actions {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-actions .el-tag {
  margin-right: 10px;
}

@media (max-width: 768px) {
  .category-header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .category-header-actions .el-input {
    width: 100% !important;
    margin-right: 0 !important;
  }
  
  .pagination-container {
    justify-content: center;
  }
  
  .batch-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .batch-actions .el-tag {
    margin-right: 0;
    margin-bottom: 10px;
  }
}
</style>
