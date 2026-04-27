<template>
  <div class="user-management-container">
    <h2>用户角色管理</h2>
    
    <el-tabs v-model="store.activeTab">
      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <user-management-tab />
      </el-tab-pane>
      
      <!-- 角色管理 -->
      <el-tab-pane label="角色管理" name="roles">
        <role-management-tab />
      </el-tab-pane>
      
      <!-- 权限管理 -->
      <el-tab-pane label="权限管理" name="permissions">
        <permission-management-tab />
      </el-tab-pane>
    </el-tabs>
    
    <!-- 用户对话框 -->
    <user-dialog />
    
    <!-- 分配角色对话框 -->
    <assign-role-dialog />
    
    <!-- 角色对话框 -->
    <role-dialog />
    
    <!-- 权限对话框 -->
    <permission-dialog />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

import UserManagementTab from './components/UserManagementTab.vue'
import RoleManagementTab from './components/RoleManagementTab.vue'
import PermissionManagementTab from './components/PermissionManagementTab.vue'
import UserDialog from './components/UserDialog.vue'
import AssignRoleDialog from './components/AssignRoleDialog.vue'
import RoleDialog from './components/RoleDialog.vue'
import PermissionDialog from './components/PermissionDialog.vue'

const store = useUserStore()

onMounted(() => {
  store.getUsers()
  store.getRoles()
  store.getPermissions()
})
</script>

<style scoped>
.user-management-container {
  padding: 20px;
}

@media (max-width: 768px) {
  .user-management-container {
    padding: 10px;
  }
}
</style>
