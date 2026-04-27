<template>
  <el-dialog v-model="store.detailDialogVisible" title="图书详情" width="800px">
    <el-descriptions :column="2" border v-if="store.currentBook">
      <el-descriptions-item label="ID">{{ store.currentBook.id }}</el-descriptions-item>
      <el-descriptions-item label="条码">{{ store.currentBook.barcode }}</el-descriptions-item>
      <el-descriptions-item label="标题">{{ store.currentBook.title }}</el-descriptions-item>
      <el-descriptions-item label="作者">{{ store.currentBook.author }}</el-descriptions-item>
      <el-descriptions-item label="出版社">{{ store.currentBook.publisher }}</el-descriptions-item>
      <el-descriptions-item label="丛书">{{ store.currentBook.series || '-' }}</el-descriptions-item>
      <el-descriptions-item label="价格">¥{{ store.currentBook.price?.toFixed(2) || '0.00' }}</el-descriptions-item>
      <el-descriptions-item label="库存">
        <el-tag :type="store.getStockTagType(store.currentBook.stock)">
          {{ store.currentBook.stock }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="折扣">{{ Math.round((store.currentBook.discount || 0) * 100) }}%</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ store.currentBook.created_at }}</el-descriptions-item>
      <el-descriptions-item label="更新时间">{{ store.currentBook.updated_at }}</el-descriptions-item>
      <el-descriptions-item label="简介" :span="2">
        <el-popover placement="top" :width="600" trigger="hover">
          <template #reference>
            <span>{{ store.currentBook.summary ? (store.currentBook.summary.length > 100 ? store.currentBook.summary.substring(0, 100) + '...' : store.currentBook.summary) : '-' }}</span>
          </template>
          <pre>{{ store.currentBook.summary || '-' }}</pre>
        </el-popover>
      </el-descriptions-item>
    </el-descriptions>
  </el-dialog>
</template>

<script setup>
import { useBookStore } from '@/stores/book'

const store = useBookStore()
</script>
