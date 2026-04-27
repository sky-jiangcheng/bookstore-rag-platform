<template>
  <el-dialog v-model="store.purchaseDetailVisible" title="采购单详情" width="800px">
    <div v-if="store.currentPurchaseOrder">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="订单编号">{{ store.currentPurchaseOrder.order_number }}</el-descriptions-item>
        <el-descriptions-item label="供应商">{{ store.currentPurchaseOrder.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="总金额">{{ store.currentPurchaseOrder.total_amount.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="订单状态">
          <el-tag :type="store.getStatusTagType(store.currentPurchaseOrder.status)">
            {{ store.getStatusLabel(store.currentPurchaseOrder.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="下单日期">{{ store.currentPurchaseOrder.order_date }}</el-descriptions-item>
        <el-descriptions-item label="预计送达">{{ store.currentPurchaseOrder.expected_delivery_date }}</el-descriptions-item>
        <el-descriptions-item label="实际送达">{{ store.currentPurchaseOrder.actual_delivery_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ store.currentPurchaseOrder.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <h3 style="margin-top: 20px;">采购明细</h3>
      <el-table :data="store.currentPurchaseOrder.items" border style="width: 100%;">
        <el-table-column prop="book_id" label="书籍ID" width="100" />
        <el-table-column prop="book_title" label="书籍名称" min-width="200" />
        <el-table-column prop="quantity" label="数量" width="100" />
        <el-table-column prop="unit_price" label="单价" width="100">
          <template #default="scope">
            <span>{{ scope.row.unit_price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_price" label="金额" width="120">
          <template #default="scope">
            <span>{{ scope.row.total_price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="200" />
      </el-table>
    </div>
  </el-dialog>
</template>

<script setup>
import { usePurchaseStore } from '@/stores/purchase'

const store = usePurchaseStore()
</script>
