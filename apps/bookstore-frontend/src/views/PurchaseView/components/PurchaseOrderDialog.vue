<template>
  <el-dialog v-model="store.purchaseDialogVisible" title="新增采购单" width="800px">
    <el-form :model="store.purchaseForm" label-width="100px">
      <el-form-item label="供应商" required>
        <el-select v-model="store.purchaseForm.supplier_id" placeholder="请选择供应商" style="width: 100%;">
          <el-option
            v-for="supplier in store.supplierOptions"
            :key="supplier.id"
            :label="supplier.name"
            :value="supplier.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="预计送达日期">
        <el-date-picker
          v-model="store.purchaseForm.expected_delivery_date"
          type="datetime"
          placeholder="选择预计送达日期"
          style="width: 100%;"
        />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="store.purchaseForm.remark" placeholder="请输入备注" type="textarea" :rows="3" />
      </el-form-item>
      
      <el-form-item label="采购明细" required>
        <el-button type="primary" @click="store.addPurchaseItem" style="margin-bottom: 10px;">
          <el-icon><Plus /></el-icon>
          新增明细
        </el-button>
        
        <el-table :data="store.purchaseForm.items" border style="width: 100%;">
          <el-table-column label="书籍" width="300">
            <template #default="scope">
              <el-select v-model="scope.row.book_id" placeholder="请选择书籍" style="width: 100%;">
                <el-option
                  v-for="book in store.bookOptions"
                  :key="book.id"
                  :label="book.title"
                  :value="book.id"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="120">
            <template #default="scope">
              <el-input-number v-model="scope.row.quantity" :min="1" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="scope">
              <el-input v-model.number="scope.row.unit_price" type="number" :min="0" step="0.01" />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="120">
            <template #default="scope">
              <span>{{ (scope.row.quantity * scope.row.unit_price).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="scope">
              <el-button type="danger" size="small" @click="store.removePurchaseItem(scope.$index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.purchaseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { Plus, Delete } from '@element-plus/icons-vue'
import { usePurchaseStore } from '@/stores/purchase'
import { ElMessage } from 'element-plus'

const store = usePurchaseStore()

const handleSave = async () => {
  const result = await store.savePurchaseOrder()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}
</script>
