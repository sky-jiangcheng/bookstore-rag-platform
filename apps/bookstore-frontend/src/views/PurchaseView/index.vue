<template>
  <div class="purchase-container">
    <h2>采购管理</h2>
    
    <el-tabs v-model="store.activeTab">
      <!-- 供应商管理 -->
      <el-tab-pane label="供应商管理" name="suppliers">
        <supplier-management-tab />
      </el-tab-pane>
      
      <!-- 采购单管理 -->
      <el-tab-pane label="采购单管理" name="purchaseOrders">
        <purchase-order-tab />
      </el-tab-pane>
    </el-tabs>
    
    <!-- 供应商对话框 -->
    <supplier-dialog />
    
    <!-- 采购单对话框 -->
    <purchase-order-dialog />
    
    <!-- 采购单详情对话框 -->
    <purchase-detail-dialog />
    
    <!-- 更新订单状态对话框 -->
    <status-dialog />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { usePurchaseStore } from '@/stores/purchase'

import SupplierManagementTab from './components/SupplierManagementTab.vue'
import PurchaseOrderTab from './components/PurchaseOrderTab.vue'
import SupplierDialog from './components/SupplierDialog.vue'
import PurchaseOrderDialog from './components/PurchaseOrderDialog.vue'
import PurchaseDetailDialog from './components/PurchaseDetailDialog.vue'
import StatusDialog from './components/StatusDialog.vue'

const store = usePurchaseStore()

onMounted(() => {
  store.getSuppliers()
  store.getPurchaseOrders()
  store.getSupplierOptions()
  store.getBookOptions()
})
</script>

<style scoped>
.purchase-container {
  padding: 20px;
}

@media (max-width: 768px) {
  .purchase-container {
    padding: 10px;
  }
}
</style>
