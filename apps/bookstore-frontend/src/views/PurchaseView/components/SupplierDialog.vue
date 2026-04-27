<template>
  <el-dialog v-model="store.supplierDialogVisible" :title="store.supplierDialogTitle" width="600px">
    <el-form :model="store.supplierForm" label-width="100px">
      <el-form-item label="供应商名称" required>
        <el-input v-model="store.supplierForm.name" placeholder="请输入供应商名称" />
      </el-form-item>
      <el-form-item label="联系人" required>
        <el-input v-model="store.supplierForm.contact_person" placeholder="请输入联系人" />
      </el-form-item>
      <el-form-item label="联系电话" required>
        <el-input v-model="store.supplierForm.phone" placeholder="请输入联系电话" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="store.supplierForm.email" placeholder="请输入邮箱" />
      </el-form-item>
      <el-form-item label="地址">
        <el-input v-model="store.supplierForm.address" placeholder="请输入地址" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="税号">
        <el-input v-model="store.supplierForm.tax_number" placeholder="请输入税号" />
      </el-form-item>
      <el-form-item label="银行账号">
        <el-input v-model="store.supplierForm.bank_account" placeholder="请输入银行账号" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="store.supplierForm.remark" placeholder="请输入备注" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.supplierDialogVisible = false">取消</el-button>
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
  const result = await store.saveSupplier()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}
</script>
