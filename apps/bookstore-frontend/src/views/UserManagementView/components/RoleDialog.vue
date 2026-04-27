<template>
  <el-dialog v-model="store.roleDialogVisible" :title="store.isAddMode ? '新增角色' : '编辑角色'" width="500px">
    <el-form :model="store.roleForm" label-width="80px">
      <el-form-item label="角色名称" required>
        <el-input v-model="store.roleForm.name" placeholder="请输入角色名称" />
      </el-form-item>
      <el-form-item label="角色代码" required>
        <el-input v-model="store.roleForm.code" placeholder="请输入角色代码" :disabled="!store.isAddMode" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="store.roleForm.description" placeholder="请输入角色描述" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.roleDialogVisible = false">取消</el-button>
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
  const result = await store.saveRole()
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
