<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>用户列表</span>
        <el-button type="primary" @click="store.openAddUserDialog">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </div>
    </template>
    
    <!-- 搜索表单 -->
    <el-form :inline="true" :model="store.userSearchForm" class="filter-form" style="margin-bottom: 20px;">
      <el-form-item label="用户名">
        <el-input v-model="store.userSearchForm.username" placeholder="请输入用户名" clearable />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input v-model="store.userSearchForm.name" placeholder="请输入姓名" clearable />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="store.userSearchForm.email" placeholder="请输入邮箱" clearable />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="store.userSearchForm.is_active" placeholder="请选择状态" clearable>
          <el-option label="激活" value="true" />
          <el-option label="禁用" value="false" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
    
    <!-- 用户表格 -->
    <el-table v-loading="store.userLoading" :data="store.userList" style="width: 100%" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="email" label="邮箱" width="200" />
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
            {{ scope.row.is_active ? '激活' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="roles" label="角色" min-width="150">
        <template #default="scope">
          <div class="role-tags">
            <el-tag size="small" v-for="role in scope.row.roles" :key="role.id" class="role-tag">
              {{ role.name }}
            </el-tag>
            <span v-if="!scope.row.roles?.length">-</span>
          </div>
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
          <el-button type="warning" size="small" @click="handleAssignRole(scope.row)">分配角色</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination" style="margin-top: 20px;">
      <el-pagination
        v-model:current-page="store.userPagination.currentPage"
        v-model:page-size="store.userPagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="store.userPagination.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const store = useUserStore()

const handleSearch = async () => {
  const result = await store.searchUsers()
  if (!result.success) ElMessage.error(result.message)
}

const handleReset = async () => {
  const result = await store.resetUserSearch()
  if (!result.success) ElMessage.error(result.message)
}

const handleSizeChange = async (size) => {
  const result = await store.handleUserSizeChange(size)
  if (!result.success) ElMessage.error(result.message)
}

const handleCurrentChange = async (current) => {
  const result = await store.handleUserCurrentChange(current)
  if (!result.success) ElMessage.error(result.message)
}

const handleView = (user) => {
  store.viewUserDetail(user)
}

const handleEdit = (user) => {
  store.openEditUserDialog(user)
}

const handleAssignRole = (user) => {
  store.openUpdateUserRolesDialog(user)
}
</script>

<style scoped>
.role-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.role-tag {
  margin-right: 5px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
