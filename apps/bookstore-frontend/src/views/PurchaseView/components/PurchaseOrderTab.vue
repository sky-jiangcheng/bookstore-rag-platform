<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>采购单列表</span>
        <el-button type="primary" @click="store.openAddPurchaseOrderDialog">
          <el-icon><Plus /></el-icon>
          新增采购单
        </el-button>
      </div>
    </template>
    
    <el-form :inline="true" :model="store.purchaseFilter" class="filter-form" style="margin-bottom: 20px;">
      <el-form-item label="订单编号">
        <el-input v-model="store.purchaseFilter.order_number" placeholder="请输入订单编号" clearable />
      </el-form-item>
      <el-form-item label="供应商">
        <el-select v-model="store.purchaseFilter.supplier_id" placeholder="请选择供应商" clearable>
          <el-option
            v-for="supplier in store.supplierOptions"
            :key="supplier.id"
            :label="supplier.name"
            :value="supplier.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="订单状态">
        <el-select v-model="store.purchaseFilter.status" placeholder="请选择订单状态" clearable>
          <el-option label="待处理" value="PENDING" />
          <el-option label="已批准" value="APPROVED" />
          <el-option label="已下单" value="ORDERED" />
          <el-option label="已送达" value="DELIVERED" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="已取消" value="CANCELLED" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
    
    <el-table v-loading="store.purchaseLoading" :data="store.purchaseData" style="width: 100%" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="order_number" label="订单编号" min-width="180" />
      <el-table-column prop="supplier_name" label="供应商" min-width="150" />
      <el-table-column prop="total_amount" label="总金额" width="120">
        <template #default="scope">
          <span class="amount">{{ scope.row.total_amount.toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="订单状态" width="120">
        <template #default="scope">
          <el-tag :type="store.getStatusTagType(scope.row.status)">
            {{ store.getStatusLabel(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="order_date" label="下单日期" width="180" />
      <el-table-column prop="expected_delivery_date" label="预计送达" width="180" />
      <el-table-column prop="actual_delivery_date" label="实际送达" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="store.viewPurchaseOrder(scope.row)">查看</el-button>
          <el-button size="small" type="primary" @click="store.updateOrderStatus(scope.row)">更新状态</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination" style="margin-top: 20px;">
      <el-pagination
        v-model:current-page="store.purchasePage"
        v-model:page-size="store.purchaseLimit"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="store.purchaseTotal"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { Plus } from '@element-plus/icons-vue'
import { usePurchaseStore } from '@/stores/purchase'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = usePurchaseStore()

const handleSearch = async () => {
  const result = await store.getPurchaseOrders()
  if (!result.success) ElMessage.error(result.message)
}

const handleReset = async () => {
  const result = await store.resetPurchaseFilter()
  if (!result.success) ElMessage.error(result.message)
}

const handleSizeChange = async (size) => {
  const result = await store.handlePurchaseSizeChange(size)
  if (!result.success) ElMessage.error(result.message)
}

const handleCurrentChange = async (current) => {
  const result = await store.handlePurchaseCurrentChange(current)
  if (!result.success) ElMessage.error(result.message)
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该采购单吗？', '提示', { type: 'warning' })
    const result = await store.deletePurchaseOrder(id)
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.amount {
  color: #f56c6c;
  font-weight: bold;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
