<template>
  <el-card class="search-card">
    <el-form :inline="true" :model="store.searchForm" class="search-form">
      <el-form-item label="图书标题">
        <el-input v-model="store.searchForm.title" placeholder="请输入图书标题" clearable />
      </el-form-item>
      <el-form-item label="作者">
        <el-input v-model="store.searchForm.author" placeholder="请输入作者" clearable />
      </el-form-item>
      <el-form-item label="出版社">
        <el-input v-model="store.searchForm.publisher" placeholder="请输入出版社" clearable />
      </el-form-item>
      <el-form-item label="条码">
        <el-input v-model="store.searchForm.barcode" placeholder="请输入条码" clearable />
      </el-form-item>
      <el-form-item label="库存范围">
        <el-input-number v-model="store.searchForm.minStock" placeholder="最小" :min="0" style="width: 100px;" />
        <span style="margin: 0 10px;">-</span>
        <el-input-number v-model="store.searchForm.maxStock" placeholder="最大" :min="0" style="width: 100px;" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'
import { useBookStore } from '@/stores/book'
import { ElMessage } from 'element-plus'

const store = useBookStore()

const handleSearch = async () => {
  const result = await store.searchBooks()
  if (!result.success) {
    ElMessage.error(result.message)
  }
}

const handleReset = async () => {
  const result = await store.resetSearch()
  if (!result.success) {
    ElMessage.error(result.message)
  }
}
</script>

<style scoped>
.search-card {
  margin-bottom: 20px;
}

.search-form {
  margin-bottom: 10px;
}
</style>
