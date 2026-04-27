<template>
  <div class="user-management-container">
    <h2>用户角色管理</h2>
    
    <el-tabs v-model="activeTab">
      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>用户列表</span>
              <el-button type="primary" @click="openAddUserDialog">
                <el-icon><Plus /></el-icon>
                新增用户
              </el-button>
            </div>
          </template>
          
          <!-- 搜索表单 -->
          <el-form :inline="true" :model="userSearchForm" class="filter-form" style="margin-bottom: 20px;">
            <el-form-item label="用户名">
              <el-input v-model="userSearchForm.username" placeholder="请输入用户名" clearable />
            </el-form-item>
            <el-form-item label="姓名">
              <el-input v-model="userSearchForm.name" placeholder="请输入姓名" clearable />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="userSearchForm.email" placeholder="请输入邮箱" clearable />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="userSearchForm.is_active" placeholder="请选择状态" clearable>
                <el-option label="激活" value="true" />
                <el-option label="禁用" value="false" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="getUsers">查询</el-button>
              <el-button @click="resetUserSearch">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 用户表格 -->
          <el-table
            v-loading="userLoading"
            :data="userList"
            style="width: 100%"
            border
          >
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
                  <span v-if="scope.row.roles.length === 0">-</span>
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
                <el-button size="small" @click="viewUserDetail(scope.row)">查看</el-button>
                <el-button type="primary" size="small" @click="openEditUserDialog(scope.row)">编辑</el-button>
                <el-button type="warning" size="small" @click="openUpdateUserRolesDialog(scope.row)">
                  分配角色
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination" style="margin-top: 20px;">
            <el-pagination
              :current-page.sync="userPagination.currentPage"
              :page-size.sync="userPagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="userPagination.total"
              @size-change="handleUserSizeChange"
              @current-change="handleUserCurrentChange"
            />
          </div>
        </el-card>
      </el-tab-pane>
      
      <!-- 角色管理 -->
      <el-tab-pane label="角色管理" name="roles">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>角色列表</span>
              <el-button type="primary" @click="openAddRoleDialog">
                <el-icon><Plus /></el-icon>
                新增角色
              </el-button>
            </div>
          </template>
          
          <!-- 搜索表单 -->
          <el-form :inline="true" :model="roleSearchForm" class="filter-form" style="margin-bottom: 20px;">
            <el-form-item label="角色名称">
              <el-input v-model="roleSearchForm.name" placeholder="请输入角色名称" clearable />
            </el-form-item>
            <el-form-item label="角色代码">
              <el-input v-model="roleSearchForm.code" placeholder="请输入角色代码" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="getRoles">查询</el-button>
              <el-button @click="resetRoleSearch">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 角色表格 -->
          <el-table
            v-loading="roleLoading"
            :data="roleList"
            style="width: 100%"
            border
          >
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
                <el-button size="small" @click="viewRoleDetail(scope.row)">查看</el-button>
                <el-button type="primary" size="small" @click="openEditRoleDialog(scope.row)">编辑</el-button>
                <el-button type="danger" size="small" @click="deleteRole(scope.row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination" style="margin-top: 20px;">
            <el-pagination
              :current-page.sync="rolePagination.currentPage"
              :page-size.sync="rolePagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="rolePagination.total"
              @size-change="handleRoleSizeChange"
              @current-change="handleRoleCurrentChange"
            />
          </div>
        </el-card>
      </el-tab-pane>
      
      <!-- 权限管理 -->
      <el-tab-pane label="权限管理" name="permissions">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>权限列表</span>
            </div>
          </template>
          
          <!-- 搜索表单 -->
          <el-form :inline="true" :model="permissionSearchForm" class="filter-form" style="margin-bottom: 20px;">
            <el-form-item label="权限名称">
              <el-input v-model="permissionSearchForm.name" placeholder="请输入权限名称" clearable />
            </el-form-item>
            <el-form-item label="权限代码">
              <el-input v-model="permissionSearchForm.code" placeholder="请输入权限代码" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="getPermissions">查询</el-button>
              <el-button @click="resetPermissionSearch">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 权限表格 -->
          <el-table
            v-loading="permissionLoading"
            :data="permissionList"
            style="width: 100%"
            border
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="权限名称" width="180" />
            <el-table-column prop="code" label="权限代码" width="180" />
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="scope">
                <span>{{ scope.row.created_at ? new Date(scope.row.created_at).toLocaleString() : '-' }}</span>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination" style="margin-top: 20px;">
            <el-pagination
              :current-page.sync="permissionPagination.currentPage"
              :page-size.sync="permissionPagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="permissionPagination.total"
              @size-change="handlePermissionSizeChange"
              @current-change="handlePermissionCurrentChange"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 用户详情对话框 -->
    <el-dialog v-model="userDetailDialogVisible" title="用户详情" width="600px">
      <el-descriptions :column="2" border v-if="currentUser">
        <el-descriptions-item label="ID">{{ currentUser.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ currentUser.username }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ currentUser.name }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ currentUser.email }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentUser.is_active ? 'success' : 'danger'">
            {{ currentUser.is_active ? '激活' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <div class="role-tags">
            <el-tag size="small" v-for="role in currentUser.roles" :key="role.id" class="role-tag">
              {{ role.name }}
            </el-tag>
            <span v-if="currentUser.roles.length === 0">-</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentUser.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ currentUser.updated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
    
    <!-- 编辑用户对话框 -->
    <el-dialog v-model="userEditDialogVisible" :title="isAddUser ? '新增用户' : '编辑用户'" width="500px">
      <el-form :model="userForm" label-width="100px">
        <el-form-item label="用户名" required v-if="isAddUser">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="userForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="userForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="userEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveUser">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 分配角色对话框 -->
    <el-dialog v-model="userRolesDialogVisible" title="分配角色" width="600px">
      <el-form v-if="currentUser">
        <el-form-item label="用户名">
          <el-input v-model="currentUser.username" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="currentUser.name" disabled />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-checkbox-group v-model="selectedRoles">
            <el-checkbox v-for="role in allRoles" :key="role.id" :label="role.id">
              {{ role.name }} ({{ role.code }})
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="userRolesDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveUserRoles">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 角色详情对话框 -->
    <el-dialog v-model="roleDetailDialogVisible" title="角色详情" width="600px">
      <el-descriptions :column="2" border v-if="currentRole">
        <el-descriptions-item label="ID">{{ currentRole.id }}</el-descriptions-item>
        <el-descriptions-item label="角色名称">{{ currentRole.name }}</el-descriptions-item>
        <el-descriptions-item label="角色代码">{{ currentRole.code }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ currentRole.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="权限" :span="2">
          <div class="permission-tags">
            <el-tag size="small" v-for="perm in currentRole.permissions" :key="perm.id" class="permission-tag">
              {{ perm.name }} ({{ perm.code }})
            </el-tag>
            <span v-if="currentRole.permissions.length === 0">-</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentRole.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ currentRole.updated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
    
    <!-- 编辑角色对话框 -->
    <el-dialog v-model="roleEditDialogVisible" :title="isAddRole ? '新增角色' : '编辑角色'" width="600px">
      <el-form :model="roleForm" label-width="100px">
        <el-form-item label="角色名称" required>
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色代码" required>
          <el-input v-model="roleForm.code" placeholder="请输入角色代码" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="roleForm.description" placeholder="请输入角色描述" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="权限" v-if="allPermissions.length > 0">
          <el-checkbox-group v-model="selectedPermissions">
            <el-checkbox v-for="perm in allPermissions" :key="perm.id" :label="perm.id">
              {{ perm.name }} ({{ perm.code }})
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="roleEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveRole">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import request from '../utils/request'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Delete, User, Key, Lock } from '@element-plus/icons-vue'

// 标签页
const activeTab = ref('users')

// 用户管理
const userList = ref([])
const userLoading = ref(false)
const userSearchForm = reactive({
  username: '',
  name: '',
  email: '',
  is_active: null
})
const userPagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})
const userDetailDialogVisible = ref(false)
const userEditDialogVisible = ref(false)
const userRolesDialogVisible = ref(false)
const currentUser = ref(null)
const isAddUser = ref(false)
const userForm = reactive({
  id: null,
  username: '',
  name: '',
  email: '',
  is_active: true
})
const selectedRoles = ref([])
const allRoles = ref([])

// 角色管理
const roleList = ref([])
const roleLoading = ref(false)
const roleSearchForm = reactive({
  name: '',
  code: ''
})
const rolePagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})
const roleDetailDialogVisible = ref(false)
const roleEditDialogVisible = ref(false)
const currentRole = ref(null)
const isAddRole = ref(false)
const roleForm = reactive({
  id: null,
  name: '',
  code: '',
  description: ''
})
const selectedPermissions = ref([])
const allPermissions = ref([])

// 权限管理
const permissionList = ref([])
const permissionLoading = ref(false)
const permissionSearchForm = reactive({
  name: '',
  code: ''
})
const permissionPagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 获取用户列表
const getUsers = async () => {
  userLoading.value = true
  try {
    const params = {
      username: userSearchForm.username || undefined,
      name: userSearchForm.name || undefined,
      email: userSearchForm.email || undefined,
      is_active: userSearchForm.is_active !== null ? userSearchForm.is_active : undefined,
      page: userPagination.currentPage,
      limit: userPagination.pageSize
    }
    
    const response = await request.get('/users', { params })
    userList.value = response.data.items
    userPagination.total = response.data.total
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    userLoading.value = false
  }
}

// 重置用户搜索
const resetUserSearch = () => {
  Object.assign(userSearchForm, {
    username: '',
    name: '',
    email: '',
    is_active: null
  })
  userPagination.currentPage = 1
  getUsers()
}

// 分页处理
const handleUserSizeChange = (size) => {
  userPagination.pageSize = size
  getUsers()
}

const handleUserCurrentChange = (current) => {
  userPagination.currentPage = current
  getUsers()
}

// 查看用户详情
const viewUserDetail = async (user) => {
  try {
    const response = await request.get(`/users/${user.id}`)
    currentUser.value = response.data
    userDetailDialogVisible.value = true
  } catch (error) {
    console.error('获取用户详情失败:', error)
    ElMessage.error('获取用户详情失败')
  }
}

// 打开编辑用户对话框
const openEditUserDialog = (user) => {
  isAddUser.value = false
  Object.assign(userForm, {
    id: user.id,
    username: user.username,
    name: user.name,
    email: user.email,
    is_active: user.is_active
  })
  userEditDialogVisible.value = true
}

// 打开新增用户对话框
const openAddUserDialog = () => {
  isAddUser.value = true
  Object.assign(userForm, {
    id: null,
    username: '',
    name: '',
    email: '',
    is_active: true
  })
  userEditDialogVisible.value = true
}

// 保存用户
const saveUser = async () => {
  if (!userForm.name || !userForm.email) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  try {
    if (isAddUser.value) {
      // 新增用户（暂时提示功能开发中）
      ElMessage.success('新增用户功能开发中')
    } else {
      // 更新用户
      await request.put(`/users/${userForm.id}`, userForm)
      ElMessage.success('用户信息更新成功')
      getUsers()
    }
    userEditDialogVisible.value = false
  } catch (error) {
    console.error('保存用户失败:', error)
    ElMessage.error('保存用户失败')
  }
}

// 打开分配角色对话框
const openUpdateUserRolesDialog = async (user) => {
  try {
    // 获取所有角色
    await getRoles()
    currentUser.value = user
    selectedRoles.value = user.roles.map(role => role.id)
    userRolesDialogVisible.value = true
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取角色列表失败')
  }
}

// 保存用户角色
const saveUserRoles = async () => {
  try {
    await request.put(`/users/${currentUser.value.id}/roles`, {
      roles: selectedRoles.value
    })
    ElMessage.success('用户角色更新成功')
    getUsers()
    userRolesDialogVisible.value = false
  } catch (error) {
    console.error('更新用户角色失败:', error)
    ElMessage.error('更新用户角色失败')
  }
}

// 获取角色列表
const getRoles = async () => {
  roleLoading.value = true
  try {
    const params = {
      name: roleSearchForm.name || undefined,
      code: roleSearchForm.code || undefined,
      page: rolePagination.currentPage,
      limit: rolePagination.pageSize
    }
    
    const response = await request.get('/roles', { params })
    if (activeTab.value === 'roles') {
      roleList.value = response.data.items
      rolePagination.total = response.data.total
    } else {
      allRoles.value = response.data.items
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取角色列表失败')
  } finally {
    roleLoading.value = false
  }
}

// 重置角色搜索
const resetRoleSearch = () => {
  Object.assign(roleSearchForm, {
    name: '',
    code: ''
  })
  rolePagination.currentPage = 1
  getRoles()
}

// 分页处理
const handleRoleSizeChange = (size) => {
  rolePagination.pageSize = size
  getRoles()
}

const handleRoleCurrentChange = (current) => {
  rolePagination.currentPage = current
  getRoles()
}

// 查看角色详情
const viewRoleDetail = async (role) => {
  try {
    currentRole.value = role
    roleDetailDialogVisible.value = true
  } catch (error) {
    console.error('获取角色详情失败:', error)
    ElMessage.error('获取角色详情失败')
  }
}

// 打开编辑角色对话框
const openEditRoleDialog = async (role) => {
  try {
    // 获取所有权限
    await getPermissions()
    isAddRole.value = false
    Object.assign(roleForm, {
      id: role.id,
      name: role.name,
      code: role.code,
      description: role.description || ''
    })
    selectedPermissions.value = role.permissions?.map(perm => perm.id) || []
    roleEditDialogVisible.value = true
  } catch (error) {
    console.error('获取权限列表失败:', error)
    ElMessage.error('获取权限列表失败')
  }
}

// 打开新增角色对话框
const openAddRoleDialog = async () => {
  try {
    // 获取所有权限
    await getPermissions()
    isAddRole.value = true
    Object.assign(roleForm, {
      id: null,
      name: '',
      code: '',
      description: ''
    })
    selectedPermissions.value = []
    roleEditDialogVisible.value = true
  } catch (error) {
    console.error('获取权限列表失败:', error)
    ElMessage.error('获取权限列表失败')
  }
}

// 保存角色
const saveRole = async () => {
  if (!roleForm.name || !roleForm.code) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  try {
    const roleData = {
      name: roleForm.name,
      code: roleForm.code,
      description: roleForm.description,
      permissions: selectedPermissions.value
    }
    
    if (isAddRole.value) {
      // 新增角色
      await request.post('/roles', roleData)
      ElMessage.success('角色创建成功')
    } else {
      // 更新角色
      await request.put(`/roles/${roleForm.id}`, roleData)
      ElMessage.success('角色更新成功')
    }
    getRoles()
    roleEditDialogVisible.value = false
  } catch (error) {
    console.error('保存角色失败:', error)
    ElMessage.error('保存角色失败')
  }
}

// 删除角色
const deleteRole = async (id) => {
  try {
    await request.delete(`/roles/${id}`)
    ElMessage.success('角色删除成功')
    getRoles()
  } catch (error) {
    console.error('删除角色失败:', error)
    ElMessage.error('删除角色失败')
  }
}

// 获取权限列表
const getPermissions = async () => {
  permissionLoading.value = true
  try {
    const params = {
      name: permissionSearchForm.name || undefined,
      code: permissionSearchForm.code || undefined,
      page: permissionPagination.currentPage,
      limit: permissionPagination.pageSize
    }
    
    const response = await request.get('/permissions', { params })
    if (activeTab.value === 'permissions') {
      permissionList.value = response.data.items
      permissionPagination.total = response.data.total
    } else {
      allPermissions.value = response.data.items
    }
  } catch (error) {
    console.error('获取权限列表失败:', error)
    ElMessage.error('获取权限列表失败')
  } finally {
    permissionLoading.value = false
  }
}

// 重置权限搜索
const resetPermissionSearch = () => {
  Object.assign(permissionSearchForm, {
    name: '',
    code: ''
  })
  permissionPagination.currentPage = 1
  getPermissions()
}

// 分页处理
const handlePermissionSizeChange = (size) => {
  permissionPagination.pageSize = size
  getPermissions()
}

const handlePermissionCurrentChange = (current) => {
  permissionPagination.currentPage = current
  getPermissions()
}

// 初始化
onMounted(() => {
  getUsers()
})
</script>

<style scoped>
.user-management-container {
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

.role-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 5px;
}

.role-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.permission-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 5px;
}

.permission-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .filter-form {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-form .el-form-item {
    margin-bottom: 10px;
  }
}
</style>
