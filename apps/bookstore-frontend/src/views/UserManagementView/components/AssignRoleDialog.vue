<template>
  <el-dialog v-model="store.assignRoleDialogVisible" title="分配角色" width="500px">
    <el-form label-width="80px">
      <el-form-item label="用户名">
        <span>{{ store.currentUser?.username }}</span>
      </el-form-item>
      <el-form-item label="当前角色">
        <div v-if="store.currentUser?.roles?.length">
          <el-tag v-for="role in store.currentUser.roles" :key="role.id" style="margin-right: 5px;">
            {{ role.name }}
          </el-tag>
        </div>
        <span v-else>暂无角色</span>
      </el-form-item>
      <el-form-item label="选择角色">
        <el-checkbox-group v-model="store.selectedRoleIds">
          <el-checkbox v-for="role in store.roleList" :key="role.id" :label="role.id">
            {{ role.name }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.assignRoleDialogVisible = false">取消</el-button>
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
  const result = await store.assignRolesToUser()
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
