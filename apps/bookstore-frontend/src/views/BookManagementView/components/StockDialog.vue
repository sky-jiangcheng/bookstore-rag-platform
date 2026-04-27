<template>
  <el-dialog v-model="store.stockDialogVisible" title="调整库存" width="400px">
    <el-form :model="store.stockForm" label-width="80px">
      <el-form-item label="图书名称" disabled>
        <el-input v-model="store.stockForm.bookTitle" />
      </el-form-item>
      <el-form-item label="当前库存" disabled>
        <el-input v-model="store.stockForm.currentStock" />
      </el-form-item>
      <el-form-item label="新库存" required>
        <el-input-number v-model="store.stockForm.newStock" :min="0" style="width: 100%;" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.stockDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { useBookStore } from '@/stores/book'

const store = useBookStore()
const emit = defineEmits(['update'])

const handleUpdate = () => {
  emit('update')
}
</script>

<style scoped>
.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
}
</style>
