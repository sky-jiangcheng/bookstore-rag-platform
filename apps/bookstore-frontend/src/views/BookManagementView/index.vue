<template>
  <div class="book-management-container">
    <h2>图书管理</h2>
    
    <!-- 搜索表单 -->
    <search-form />
    
    <!-- 图书列表 -->
    <book-list 
      @add="handleAdd"
      @view="handleView"
      @edit="handleEdit"
      @update-stock="handleUpdateStock"
      @add-to-purchase="handleAddToPurchase"
    />
    
    <!-- 图书详情对话框 -->
    <book-detail-dialog />
    
    <!-- 编辑图书对话框 -->
    <book-edit-dialog @save="handleSaveBook" />
    
    <!-- 调整库存对话框 -->
    <stock-dialog @update="handleUpdateStockConfirm" />
    
    <!-- 采购列表 -->
    <purchase-list />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useBookStore } from '@/stores/book'
import { ElMessage } from 'element-plus'

import SearchForm from './components/SearchForm.vue'
import BookList from './components/BookList.vue'
import BookDetailDialog from './components/BookDetailDialog.vue'
import BookEditDialog from './components/BookEditDialog.vue'
import StockDialog from './components/StockDialog.vue'
import PurchaseList from './components/PurchaseList.vue'

const store = useBookStore()

// 初始化
onMounted(() => {
  store.getBooks()
})

// 处理添加
const handleAdd = () => {
  store.openAddBookDialog()
}

// 处理查看
const handleView = async (book) => {
  const result = await store.viewBookDetail(book)
  if (!result.success) {
    ElMessage.error(result.message)
  }
}

// 处理编辑
const handleEdit = (book) => {
  store.openEditBookDialog(book)
}

// 处理保存
const handleSaveBook = async () => {
  const result = await store.saveBook()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}

// 处理调整库存
const handleUpdateStock = (book) => {
  store.openUpdateStockDialog(book)
}

// 确认调整库存
const handleUpdateStockConfirm = async () => {
  const result = await store.updateStock()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}

// 处理加入采购
const handleAddToPurchase = (book) => {
  const result = store.addToPurchase(book)
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.warning(result.message)
  }
}
</script>

<style scoped>
.book-management-container {
  padding: 20px;
}

@media (max-width: 768px) {
  .book-management-container {
    padding: 10px;
  }
}
</style>
