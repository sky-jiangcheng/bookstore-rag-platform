<template>
  <el-dialog v-model="store.keywordDialogVisible" title="关键词管理" width="80%">
    <div class="keyword-management">
      <div class="keyword-header">
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
          <span>{{ store.currentCategory?.name }} - 关键词列表</span>
          <div style="display: flex; align-items: center;">
            <el-input
              v-model="store.keywordSearchQuery"
              placeholder="搜索关键词"
              style="width: 200px; margin-right: 10px"
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
            <el-button type="primary" @click="store.openAddKeywordDialog">
              新增关键词
            </el-button>
            <el-button type="success" @click="store.openBatchAddKeywordDialog">
              批量添加
            </el-button>
          </div>
        </div>
      </div>
      
      <el-table :data="store.keywords" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="keyword" label="关键词" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button 
              size="small" 
              type="danger" 
              @click="handleDelete(scope.row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-dialog>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'
import { useFilterStore } from '@/stores/filter'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = useFilterStore()

const handleSearch = async () => {
  const result = await store.viewKeywords(store.currentCategory)
  if (!result.success) ElMessage.error(result.message)
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该关键词吗？', '提示', { type: 'warning' })
    const result = await store.deleteKeyword(id)
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消
  }
}
</script>
