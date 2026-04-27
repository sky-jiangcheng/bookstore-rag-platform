<template>
  <el-dialog v-model="visible" :title="title" width="500px">
    <el-form :model="store.categoryForm" label-width="80px">
      <el-form-item label="类别名称">
        <el-input v-model="store.categoryForm.name" placeholder="请输入类别名称" />
      </el-form-item>
      <el-form-item label="类别描述">
        <el-input 
          v-model="store.categoryForm.description" 
          placeholder="请输入类别描述" 
          type="textarea" 
          :rows="3"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-switch v-model="store.categoryForm.is_active" :active-value="1" :inactive-value="0" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="handleSave">确定</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useFilterStore } from '@/stores/filter'
import { ElMessage } from 'element-plus'

const store = useFilterStore()

const visible = computed(() => store.addCategoryDialogVisible || store.editCategoryDialogVisible)
const title = computed(() => store.addCategoryDialogVisible ? '新增屏蔽类别' : '编辑屏蔽类别')

const closeDialog = () => {
  store.addCategoryDialogVisible = false
  store.editCategoryDialogVisible = false
}

const handleSave = async () => {
  const result = store.addCategoryDialogVisible 
    ? await store.createCategory()
    : await store.updateCategory()
    
  if (result.success) {
    ElMessage.success(result.message)
    closeDialog()
  } else {
    ElMessage.error(result.message)
  }
}
</script>
