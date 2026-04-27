<template>
  <el-dialog v-model="store.editDialogVisible" :title="store.isAddMode ? '新增图书' : '编辑图书'" width="600px">
    <el-form :model="store.editForm" label-width="100px">
      <el-form-item label="条码" required>
        <el-input v-model="store.editForm.barcode" placeholder="请输入条码" />
      </el-form-item>
      <el-form-item label="图书标题" required>
        <el-input v-model="store.editForm.title" placeholder="请输入图书标题" />
      </el-form-item>
      <el-form-item label="作者">
        <el-input v-model="store.editForm.author" placeholder="请输入作者" />
      </el-form-item>
      <el-form-item label="出版社">
        <el-input v-model="store.editForm.publisher" placeholder="请输入出版社" />
      </el-form-item>
      <el-form-item label="丛书">
        <el-input v-model="store.editForm.series" placeholder="请输入丛书" />
      </el-form-item>
      <el-form-item label="价格">
        <el-input v-model.number="store.editForm.price" type="number" placeholder="请输入价格" :min="0" step="0.01" />
      </el-form-item>
      <el-form-item label="库存">
        <el-input-number v-model="store.editForm.stock" :min="0" placeholder="请输入库存" />
      </el-form-item>
      <el-form-item label="折扣">
        <el-input v-model.number="store.editForm.discount" type="number" placeholder="请输入折扣" :min="0" :max="1" step="0.01" />
      </el-form-item>
      <el-form-item label="简介">
        <el-input v-model="store.editForm.summary" type="textarea" placeholder="请输入图书简介" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { useBookStore } from '@/stores/book'

const store = useBookStore()
const emit = defineEmits(['save'])

const handleSave = () => {
  emit('save')
}
</script>

<style scoped>
.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
}
</style>
