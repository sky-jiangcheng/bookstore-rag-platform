<template>
  <el-dialog v-model="store.permissionDialogVisible" :title="store.isAddMode ? '新增权限' : '编辑权限'" width="500px">
    <el-form :model="store.permissionForm" label-width="80px">
      <el-form-item label="权限名称" required>
        <el-input v-model="store.permissionForm.name" placeholder="请输入权限名称" />
      </el-form-item>
      <el-form-item label="权限代码" required>
        <el-input v-model="store.permissionForm.code" placeholder="请输入权限代码" :disabled="!store.isAddMode" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="store.permissionForm.description" placeholder="请输入权限描述" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.permissionDialogVisible = false">取消</el-button>
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
  const result = await store.savePermission()
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
