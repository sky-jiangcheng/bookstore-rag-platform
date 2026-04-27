<template>
  <el-card v-if="store.hasPurchaseItems" class="purchase-list-card" style="margin-top: 20px;">
    <template #header>
      <div class="card-header">
        <span>已选择采购书籍 ({{ store.purchaseItems.length }})</span>
        <div class="header-actions">
          <el-button @click="handleClear">清空</el-button>
          <el-button type="success" @click="handleGoToPurchase">
            前往采购
          </el-button>
        </div>
      </div>
    </template>
    <el-table :data="store.purchaseItems" style="width: 100%" border>
      <el-table-column prop="book_id" label="ID" width="80" />
      <el-table-column prop="title" label="书名" min-width="200" />
      <el-table-column prop="author" label="作者" width="150" />
      <el-table-column prop="quantity" label="数量" width="100" />
      <el-table-column prop="unit_price" label="单价" width="100">
        <template #default="scope">
          <span>¥{{ scope.row.unit_price?.toFixed(2) || '0.00' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="scope">
          <el-button type="danger" size="small" @click="handleRemove(scope.$index)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { useBookStore } from '@/stores/book'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const store = useBookStore()
const router = useRouter()

const handleClear = () => {
  const result = store.clearPurchaseItems()
  ElMessage.info(result.message)
}

const handleGoToPurchase = () => {
  // 存储采购物品到sessionStorage
  sessionStorage.setItem('purchaseItems', JSON.stringify(store.purchaseItems))
  
  // 跳转到采购页面
  router.push('/purchase')
}

const handleRemove = (index) => {
  const result = store.removePurchaseItem(index)
  ElMessage.success(result.message)
}
</script>
