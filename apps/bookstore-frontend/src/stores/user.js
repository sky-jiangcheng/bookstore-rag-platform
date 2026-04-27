import { defineStore } from 'pinia'
import request from '@/utils/request'

/**
 * 用户管理Store
 */
export const useUserStore = defineStore('user', {
  state: () => ({
    // Tab状态
    activeTab: 'users',
    
    // 用户管理
    userList: [],
    userLoading: false,
    userSearchForm: {
      username: '',
      name: '',
      email: '',
      is_active: ''
    },
    userPagination: {
      currentPage: 1,
      pageSize: 10,
      total: 0
    },
    
    // 角色管理
    roleList: [],
    roleLoading: false,
    roleSearchForm: {
      name: '',
      code: ''
    },
    rolePagination: {
      currentPage: 1,
      pageSize: 10,
      total: 0
    },
    
    // 权限管理
    permissionList: [],
    permissionLoading: false,
    permissionSearchForm: {
      name: '',
      code: ''
    },
    permissionPagination: {
      currentPage: 1,
      pageSize: 10,
      total: 0
    },
    
    // 对话框状态
    userDialogVisible: false,
    roleDialogVisible: false,
    assignRoleDialogVisible: false,
    permissionDialogVisible: false,
    isAddMode: false,
    
    // 当前编辑对象
    currentUser: null,
    currentRole: null,
    currentPermission: null,
    
    // 表单数据
    userForm: {
      id: null,
      username: '',
      name: '',
      email: '',
      is_active: true
    },
    roleForm: {
      id: null,
      name: '',
      code: '',
      description: ''
    },
    permissionForm: {
      id: null,
      name: '',
      code: '',
      description: ''
    },
    selectedRoleIds: []
  }),

  getters: {
    hasUserSelection: (state) => state.userList.length > 0,
    hasRoleSelection: (state) => state.roleList.length > 0,
    hasPermissionSelection: (state) => state.permissionList.length > 0
  },

  actions: {
    // ========== 用户管理 ==========
    async getUsers() {
      this.userLoading = true
      try {
        const params = {
          page: this.userPagination.currentPage,
          limit: this.userPagination.pageSize,
          username: this.userSearchForm.username || undefined,
          name: this.userSearchForm.name || undefined,
          email: this.userSearchForm.email || undefined,
          is_active: this.userSearchForm.is_active || undefined
        }
        const response = await request.get('/users', { params })
        this.userList = response.data.items || []
        this.userPagination.total = response.data.total || 0
        return { success: true }
      } catch (error) {
        console.error('获取用户列表失败:', error)
        return { success: false, message: '获取用户列表失败' }
      } finally {
        this.userLoading = false
      }
    },

    async searchUsers() {
      this.userPagination.currentPage = 1
      return await this.getUsers()
    },

    async resetUserSearch() {
      this.userSearchForm = {
        username: '',
        name: '',
        email: '',
        is_active: ''
      }
      this.userPagination.currentPage = 1
      return await this.getUsers()
    },

    async handleUserSizeChange(size) {
      this.userPagination.pageSize = size
      return await this.getUsers()
    },

    async handleUserCurrentChange(current) {
      this.userPagination.currentPage = current
      return await this.getUsers()
    },

    openAddUserDialog() {
      this.isAddMode = true
      this.userForm = {
        id: null,
        username: '',
        name: '',
        email: '',
        is_active: true
      }
      this.userDialogVisible = true
    },

    openEditUserDialog(user) {
      this.isAddMode = false
      this.currentUser = user
      this.userForm = {
        id: user.id,
        username: user.username,
        name: user.name,
        email: user.email,
        is_active: user.is_active
      }
      this.userDialogVisible = true
    },

    async saveUser() {
      try {
        if (this.isAddMode) {
          await request.post('/users', this.userForm)
        } else {
          await request.put(`/users/${this.userForm.id}`, this.userForm)
        }
        this.userDialogVisible = false
        await this.getUsers()
        return { success: true, message: this.isAddMode ? '新增用户成功' : '更新用户成功' }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '保存失败' }
      }
    },

    viewUserDetail(user) {
      this.currentUser = user
    },

    openUpdateUserRolesDialog(user) {
      this.currentUser = user
      this.selectedRoleIds = user.roles?.map(role => role.id) || []
      this.assignRoleDialogVisible = true
    },

    async assignRolesToUser() {
      try {
        await request.put(`/users/${this.currentUser.id}/roles`, {
          role_ids: this.selectedRoleIds
        })
        this.assignRoleDialogVisible = false
        await this.getUsers()
        return { success: true, message: '角色分配成功' }
      } catch (error) {
        return { success: false, message: '角色分配失败' }
      }
    },

    // ========== 角色管理 ==========
    async getRoles() {
      this.roleLoading = true
      try {
        const params = {
          page: this.rolePagination.currentPage,
          limit: this.rolePagination.pageSize,
          name: this.roleSearchForm.name || undefined,
          code: this.roleSearchForm.code || undefined
        }
        const response = await request.get('/roles', { params })
        this.roleList = response.data.items || []
        this.rolePagination.total = response.data.total || 0
        return { success: true }
      } catch (error) {
        console.error('获取角色列表失败:', error)
        return { success: false, message: '获取角色列表失败' }
      } finally {
        this.roleLoading = false
      }
    },

    async searchRoles() {
      this.rolePagination.currentPage = 1
      return await this.getRoles()
    },

    async resetRoleSearch() {
      this.roleSearchForm = { name: '', code: '' }
      this.rolePagination.currentPage = 1
      return await this.getRoles()
    },

    async handleRoleSizeChange(size) {
      this.rolePagination.pageSize = size
      return await this.getRoles()
    },

    async handleRoleCurrentChange(current) {
      this.rolePagination.currentPage = current
      return await this.getRoles()
    },

    openAddRoleDialog() {
      this.isAddMode = true
      this.roleForm = {
        id: null,
        name: '',
        code: '',
        description: ''
      }
      this.roleDialogVisible = true
    },

    openEditRoleDialog(role) {
      this.isAddMode = false
      this.currentRole = role
      this.roleForm = {
        id: role.id,
        name: role.name,
        code: role.code,
        description: role.description
      }
      this.roleDialogVisible = true
    },

    async saveRole() {
      try {
        if (this.isAddMode) {
          await request.post('/roles', this.roleForm)
        } else {
          await request.put(`/roles/${this.roleForm.id}`, this.roleForm)
        }
        this.roleDialogVisible = false
        await this.getRoles()
        return { success: true, message: this.isAddMode ? '新增角色成功' : '更新角色成功' }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '保存失败' }
      }
    },

    async deleteRole(roleId) {
      try {
        await request.delete(`/roles/${roleId}`)
        await this.getRoles()
        return { success: true, message: '删除角色成功' }
      } catch (error) {
        return { success: false, message: '删除角色失败' }
      }
    },

    viewRoleDetail(role) {
      this.currentRole = role
    },

    // ========== 权限管理 ==========
    async getPermissions() {
      this.permissionLoading = true
      try {
        const params = {
          page: this.permissionPagination.currentPage,
          limit: this.permissionPagination.pageSize,
          name: this.permissionSearchForm.name || undefined,
          code: this.permissionSearchForm.code || undefined
        }
        const response = await request.get('/permissions', { params })
        this.permissionList = response.data.items || []
        this.permissionPagination.total = response.data.total || 0
        return { success: true }
      } catch (error) {
        console.error('获取权限列表失败:', error)
        return { success: false, message: '获取权限列表失败' }
      } finally {
        this.permissionLoading = false
      }
    },

    async searchPermissions() {
      this.permissionPagination.currentPage = 1
      return await this.getPermissions()
    },

    async resetPermissionSearch() {
      this.permissionSearchForm = { name: '', code: '' }
      this.permissionPagination.currentPage = 1
      return await this.getPermissions()
    },

    async handlePermissionSizeChange(size) {
      this.permissionPagination.pageSize = size
      return await this.getPermissions()
    },

    async handlePermissionCurrentChange(current) {
      this.permissionPagination.currentPage = current
      return await this.getPermissions()
    },

    openAddPermissionDialog() {
      this.isAddMode = true
      this.permissionForm = {
        id: null,
        name: '',
        code: '',
        description: ''
      }
      this.permissionDialogVisible = true
    },

    openEditPermissionDialog(permission) {
      this.isAddMode = false
      this.currentPermission = permission
      this.permissionForm = {
        id: permission.id,
        name: permission.name,
        code: permission.code,
        description: permission.description
      }
      this.permissionDialogVisible = true
    },

    async savePermission() {
      try {
        if (this.isAddMode) {
          await request.post('/permissions', this.permissionForm)
        } else {
          await request.put(`/permissions/${this.permissionForm.id}`, this.permissionForm)
        }
        this.permissionDialogVisible = false
        await this.getPermissions()
        return { success: true, message: this.isAddMode ? '新增权限成功' : '更新权限成功' }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '保存失败' }
      }
    },

    async deletePermission(permissionId) {
      try {
        await request.delete(`/permissions/${permissionId}`)
        await this.getPermissions()
        return { success: true, message: '删除权限成功' }
      } catch (error) {
        return { success: false, message: '删除权限失败' }
      }
    }
  }
})
