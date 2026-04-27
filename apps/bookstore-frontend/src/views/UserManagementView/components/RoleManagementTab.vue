<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>角色列表</span>
        <el-button type="primary" @click="store.openAddRoleDialog">
          <el-icon><Plus /></el-icon>
          新增角色
        </el-button>
      </div>
    </template>
    
    <!-- 搜索表单 -->
    <el-form :inline="true" :model="store.roleSearchForm" class="filter-form" style="margin-bottom: 20px;">
      <el-form-item label="角色名称">
        <el-input v-model="store.roleSearchForm.name" placeholder="请输入角色名称" clearable />
      </el-form-item>
      <el-form-item label="角色代码">
        <el-input v-model="store.roleSearchForm.code" placeholder="请输入角色代码" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
    
    <!-- 角色表格 -->
    <el-table v-loading="store.roleLoading" :data="store.roleList" style="width: 100%" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="角色名称" width="150" />
      <el-table-column prop="code" label="角色代码" width="150" />
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column prop="permissions" label="权限数量" width="120">
        <template #default="scope">
          <span>{{ scope.row.permissions?.length || 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="scope">
          <span>{{ scope.row.created_at ? new Date(scope.row.created_at).toLocaleString() : '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="handleView(scope.row)">查看</el-button>
          <el-button type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination" style="margin-top: 20px;">
      <el-pagination
        v-model:current-page="store.rolePagination.currentPage"
        v-model:page-size="store.rolePagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="store.rolePagination.total"
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
  const result = await store.searchRoles()
  if (!result.success) ElMessage.error(result.message)
}

const handleReset = async () => {
  const result = await store.resetRoleSearch()
  if (!result.success) ElMessage.error(result.message)
}

const handleSizeChange = async (size) => {
  const result = await store.handleRoleSizeChange(size)
  if (!result.success) ElMessage.error(result.message)
}

const handleCurrentChange = async (current) => {
  const result = await store.handleRoleCurrentChange(current)
  if (!result.success) ElMessage.error(result.message)
}

const handleView = (role) => {
  store.viewRoleDetail(role)
}

const handleEdit = (role) => {
  store.openEditRoleDialog(role)
}

const handleDelete = async (roleId) => {
  try {
    await ElMessageBox.confirm('确定要删除该角色吗？', '提示', { type: 'warning' })
    const result = await store.deleteRole(roleId)
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
