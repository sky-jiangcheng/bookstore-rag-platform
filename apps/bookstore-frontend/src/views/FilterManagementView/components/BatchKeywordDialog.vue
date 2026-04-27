<template>
  <el-dialog v-model="store.batchKeywordDialogVisible" title="批量添加关键词" width="500px">
    <el-form label-width="80px">
      <el-form-item label="关键词列表">
        <el-input 
          v-model="store.batchKeywords"
          type="textarea"
          :rows="6"
          placeholder="请输入关键词，每行一个"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.batchKeywordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确定</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { useFilterStore } from '@/stores/filter'
import { ElMessage } from 'element-plus'

const store = useFilterStore()

const handleSave = async () => {
  const result = await store.batchCreateKeywords()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}
</script>
