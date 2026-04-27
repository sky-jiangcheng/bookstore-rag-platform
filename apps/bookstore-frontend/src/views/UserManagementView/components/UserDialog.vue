<template>
  <el-dialog v-model="store.userDialogVisible" :title="store.isAddMode ? '新增用户' : '编辑用户'" width="500px">
    <el-form :model="store.userForm" label-width="80px">
      <el-form-item label="用户名" required>
        <el-input v-model="store.userForm.username" placeholder="请输入用户名" :disabled="!store.isAddMode" />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input v-model="store.userForm.name" placeholder="请输入姓名" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="store.userForm.email" placeholder="请输入邮箱" />
      </el-form-item>
      <el-form-item label="状态">
        <el-switch v-model="store.userForm.is_active" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.userDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const store = useUserStore()

const handleSave = async () => {
  const result = await store.saveUser()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
