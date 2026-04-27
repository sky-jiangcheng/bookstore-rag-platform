<template>
  <el-dialog v-model="store.statusDialogVisible" title="更新订单状态" width="400px">
    <el-form :model="store.statusForm" label-width="100px">
      <el-form-item label="订单编号">
        <el-input v-model="store.statusForm.order_number" disabled />
      </el-form-item>
      <el-form-item label="当前状态">
        <el-input v-model="store.statusForm.current_status" disabled />
      </el-form-item>
      <el-form-item label="新状态" required>
        <el-select v-model="store.statusForm.new_status" placeholder="请选择新状态" style="width: 100%;">
          <el-option label="待处理" value="PENDING" />
          <el-option label="已批准" value="APPROVED" />
          <el-option label="已下单" value="ORDERED" />
          <el-option label="已送达" value="DELIVERED" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="已取消" value="CANCELLED" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.statusDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { usePurchaseStore } from '@/stores/purchase'
import { ElMessage } from 'element-plus'

const store = usePurchaseStore()

const handleSave = async () => {
  const result = await store.saveOrderStatus()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}
</script>
