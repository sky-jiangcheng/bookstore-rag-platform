<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>权限列表</span>
        <el-button type="primary" @click="store.openAddPermissionDialog">
          <el-icon><Plus /></el-icon>
          新增权限
        </el-button>
      </div>
    </template>
    
    <!-- 搜索表单 -->
    <el-form :inline="true" :model="store.permissionSearchForm" class="filter-form" style="margin-bottom: 20px;">
      <el-form-item label="权限名称">
        <el-input v-model="store.permissionSearchForm.name" placeholder="请输入权限名称" clearable />
      </el-form-item>
      <el-form-item label="权限代码">
        <el-input v-model="store.permissionSearchForm.code" placeholder="请输入权限代码" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
    
    <!-- 权限表格 -->
    <el-table v-loading="store.permissionLoading" :data="store.permissionList" style="width: 100%" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="权限名称" width="150" />
      <el-table-column prop="code" label="权限代码" width="150" />
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="scope">
          <span>{{ scope.row.created_at ? new Date(scope.row.created_at).toLocaleString() : '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination" style="margin-top: 20px;">
      <el-pagination
        v-model:current-page="store.permissionPagination.currentPage"
        v-model:page-size="store.permissionPagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="store.permissionPagination.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = useUserStore()

const handleSearch = async () => {
  const result = await store.searchPermissions()
  if (!result.success) ElMessage.error(result.message)
}

const handleReset = async () => {
  const result = await store.resetPermissionSearch()
  if (!result.success) ElMessage.error(result.message)
}

const handleSizeChange = async (size) => {
  const result = await store.handlePermissionSizeChange(size)
  if (!result.success) ElMessage.error(result.message)
}

const handleCurrentChange = async (current) => {
  const result = await store.handlePermissionCurrentChange(current)
  if (!result.success) ElMessage.error(result.message)
}

const handleEdit = (permission) => {
  store.openEditPermissionDialog(permission)
}

const handleDelete = async (permissionId) => {
  try {
    await ElMessageBox.confirm('确定要删除该权限吗？', '提示', { type: 'warning' })
    const result = await store.deletePermission(permissionId)
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

<style scoped>
.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
