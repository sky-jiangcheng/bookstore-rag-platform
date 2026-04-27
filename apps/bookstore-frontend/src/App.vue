<template>
  <div v-if="isAuthPage">
    <router-view />
  </div>
  <el-container v-else style="height: 100vh;">
    <el-header style="background-color: #f0f2f5; padding: 0 20px; display: flex; align-items: center; justify-content: space-between;">
      <div style="font-size: 18px; font-weight: bold;">书店智能管理系统</div>
      <el-dropdown v-if="currentUser.name">
        <span class="el-dropdown-link">
          {{ currentUser.name }} <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleProfile">个人中心</el-dropdown-item>
            <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <div v-else>
        <el-button type="primary" @click="toLogin">登录</el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" style="background-color: #f0f2f5;">
        <el-menu :default-active="activeMenu" class="el-menu-vertical-demo" @select="handleMenuSelect">
          <el-menu-item index="/import">
            <el-icon><Upload /></el-icon>
            <span>数据导入</span>
          </el-menu-item>
          
          <!-- 智能服务菜单 -->
          <el-sub-menu index="/smart-services">
            <template #title>
              <el-icon><MagicStick /></el-icon>
              <span>智能服务</span>
            </template>
            <el-menu-item index="/duplicates">
              <el-icon><Search /></el-icon>
              <span>智能查重</span>
            </el-menu-item>
            <el-menu-item index="/booklist-recommendation">
              <el-icon><ChatLineRound /></el-icon>
              <span>智能书单生成器</span>
            </el-menu-item>
            <el-menu-item index="/agent-booklist">
              <el-icon><MagicStick /></el-icon>
              <span>书单助手</span>
            </el-menu-item>
            <el-menu-item index="/filters">
              <el-icon><Close /></el-icon>
              <span>屏蔽配置</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 采购推荐菜单 -->
          <el-sub-menu index="/purchase-recommendations">
            <template #title>
              <el-icon><ShoppingCart /></el-icon>
              <span>采购推荐</span>
            </template>
            <el-menu-item index="/replenishment">
              <el-icon><Warning /></el-icon>
              <span>补货推荐</span>
            </el-menu-item>
            <el-menu-item index="/recommendation">
              <el-icon><Plus /></el-icon>
              <span>新单推荐</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 管理菜单 -->
          <el-sub-menu index="/management">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>管理中心</span>
            </template>
            <el-menu-item index="/books">
              <el-icon><Reading /></el-icon>
              <span>图书管理</span>
            </el-menu-item>
            <el-menu-item index="/purchase">
              <el-icon><Printer /></el-icon>
              <span>采购管理</span>
            </el-menu-item>
            <el-menu-item index="/users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/logs">
              <el-icon><Document /></el-icon>
              <span>日志管理</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Upload, Search, ShoppingCart, ArrowDown, Document, Printer, Reading, User, MagicStick, Setting, Warning, Plus, Close, ChatLineRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from './utils/request'

const route = useRoute()
const router = useRouter()

const currentUser = ref({
  name: ''
})

const activeMenu = computed(() => {
  return route.path
})

const isAuthPage = computed(() => {
  const authPaths = ['/login', '/register']
  return authPaths.includes(route.path)
})

const handleMenuSelect = (key) => {
  router.push(key)
}

const handleProfile = () => {
  router.push('/profile')
}

const toLogin = () => {
  router.push('/login')
}

const handleLogout = async () => {
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      await request.post('/auth/logout')
    }
    
    // 清除本地存储
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
    localStorage.removeItem('name')
    
    // 重置当前用户状态
    currentUser.value.name = ''
    
    ElMessage.success('退出登录成功')
    router.push('/login')
  } catch (error) {
    // 即使退出失败，也要清除本地存储并重定向到登录页
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
    localStorage.removeItem('name')
    
    // 重置当前用户状态
    currentUser.value.name = ''
    
    ElMessage.success('退出登录成功')
    router.push('/login')
  }
}

const fetchCurrentUser = () => {
  const token = localStorage.getItem('access_token')
  const name = localStorage.getItem('name')
  
  if (token && name) {
    currentUser.value.name = name
  } else {
    currentUser.value.name = ''
  }
}

// 监听路由变化，更新用户状态
watch(() => route.path, () => {
  fetchCurrentUser()
})

onMounted(() => {
  fetchCurrentUser()
})
</script>

<style>
.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 200px;
  min-height: 400px;
}
</style>
