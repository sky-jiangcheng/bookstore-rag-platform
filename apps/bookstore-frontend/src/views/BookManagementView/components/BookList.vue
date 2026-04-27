<template>
  <el-card class="book-list-card">
    <template #header>
      <div class="card-header">
        <span>图书列表</span>
        <div class="header-actions">
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增图书
          </el-button>
        </div>
      </div>
    </template>
    
    <el-table
      v-loading="store.loading"
      :data="store.bookList"
      style="width: 100%"
      border
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="barcode" label="条码" width="180">
        <template #default="scope">
          <span>{{ scope.row.barcode || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200">
        <template #default="scope">
          <span class="book-title">{{ scope.row.title }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="author" label="作者" width="150" />
      <el-table-column prop="publisher" label="出版社" width="180" />
      <el-table-column prop="price" label="价格" width="100">
        <template #default="scope">
          <span class="price">¥{{ scope.row.price?.toFixed(2) || '0.00' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="stock" label="库存" width="100">
        <template #default="scope">
          <el-tag :type="store.getStockTagType(scope.row.stock)">
            {{ scope.row.stock }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="discount" label="折扣" width="100">
        <template #default="scope">
          <span>{{ Math.round((scope.row.discount || 0) * 100) }}%</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="scope">
          <span>{{ scope.row.created_at ? new Date(scope.row.created_at).toLocaleString() : '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="300">
        <template #default="scope">
          <div class="action-buttons">
            <el-button size="small" @click="handleView(scope.row)">查看</el-button>
            <el-button type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="warning" size="small" @click="handleUpdateStock(scope.row)">
              调整库存
            </el-button>
            <el-button type="success" size="small" @click="handleAddToPurchase(scope.row)">
              加入采购
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination" style="margin-top: 20px;">
      <el-pagination
        v-model:current-page="store.pagination.currentPage"
        v-model:page-size="store.pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="store.pagination.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { Plus } from '@element-plus/icons-vue'
import { useBookStore } from '@/stores/book'
import { ElMessage } from 'element-plus'

const store = useBookStore()

const emit = defineEmits(['add', 'view', 'edit', 'update-stock', 'add-to-purchase'])

const handleSelectionChange = (val) => {
  store.handleSelectionChange(val)
}

const handleSizeChange = async (size) => {
  const result = await store.handleSizeChange(size)
  if (!result.success) {
    ElMessage.error(result.message)
  }
}

const handleCurrentChange = async (current) => {
  const result = await store.handleCurrentChange(current)
  if (!result.success) {
    ElMessage.error(result.message)
  }
}

const handleAdd = () => {
  emit('add')
}

const handleView = (book) => {
  emit('view', book)
}

const handleEdit = (book) => {
  emit('edit', book)
}

const handleUpdateStock = (book) => {
  emit('update-stock', book)
}

const handleAddToPurchase = (book) => {
  emit('add-to-purchase', book)
}
</script>

<style scoped>
.book-title {
  font-weight: 500;
}

.price {
  color: #409EFF;
  font-weight: 500;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
    gap: 5px;
  }
  
  .action-buttons .el-button {
    width: 100%;
  }
}
</style>
