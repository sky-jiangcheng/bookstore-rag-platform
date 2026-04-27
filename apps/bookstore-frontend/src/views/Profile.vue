<template>
  <div class="profile-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>个人中心</span>
        </div>
      </template>
      
      <el-form :model="userInfo" label-width="100px" class="profile-form">
        <el-form-item label="用户ID">
          <el-input v-model="userInfo.id" disabled />
        </el-form-item>
        
        <el-form-item label="用户名">
          <el-input v-model="userInfo.username" disabled />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="userInfo.email" disabled />
        </el-form-item>
        
        <el-form-item label="姓名">
          <el-input v-model="userInfo.name" disabled />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-tag :type="userInfo.is_active ? 'success' : 'danger'">
            {{ userInfo.is_active ? '活跃' : '禁用' }}
          </el-tag>
        </el-form-item>
        
        <el-form-item label="创建时间">
          <el-input v-model="userInfo.created_at" disabled />
        </el-form-item>
      </el-form>
      
      <div class="action-buttons">
        <el-button type="primary" @click="handleLogout">退出登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userInfo = reactive({
  id: '',
  username: '',
  email: '',
  name: '',
  is_active: false,
  created_at: ''
})

const fetchUserInfo = async () => {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    
    const response = await request.get('/auth/me')
    
    userInfo.id = response.data.id
    userInfo.username = response.data.username
    userInfo.email = response.data.email
    userInfo.name = response.data.name
    userInfo.is_active = response.data.is_active
    userInfo.created_at = response.data.created_at
  } catch (error) {
    ElMessage.error('获取用户信息失败')
    router.push('/login')
  }
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
    
    ElMessage.success('退出登录成功')
    router.push('/login')
  } catch (error) {
    // 即使退出失败，也要清除本地存储并重定向到登录页
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
    localStorage.removeItem('name')
    
    ElMessage.success('退出登录成功')
    router.push('/login')
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.profile-container {
  padding: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.profile-form {
  margin-top: 20px;
}

.action-buttons {
  margin-top: 30px;
  text-align: right;
}
</style>
