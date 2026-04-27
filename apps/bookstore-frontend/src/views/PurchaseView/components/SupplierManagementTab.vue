<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>供应商列表</span>
        <el-button type="primary" @click="store.openAddSupplierDialog">
          <el-icon><Plus /></el-icon>
          新增供应商
        </el-button>
      </div>
    </template>
    
    <el-form :inline="true" :model="store.supplierFilter" class="filter-form" style="margin-bottom: 20px;">
      <el-form-item label="供应商名称">
        <el-input v-model="store.supplierFilter.name" placeholder="请输入供应商名称" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
    
    <el-table v-loading="store.supplierLoading" :data="store.supplierData" style="width: 100%" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="供应商名称" min-width="150" />
      <el-table-column prop="contact_person" label="联系人" width="120" />
      <el-table-column prop="phone" label="联系电话" width="150" />
      <el-table-column prop="email" label="邮箱" width="180" />
      <el-table-column prop="address" label="地址" min-width="200" />
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="150">
        <template #default="scope">
          <el-button type="primary" size="small" @click="store.openEditSupplierDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination" style="margin-top: 20px;">
      <el-pagination
        v-model:current-page="store.supplierPage"
        v-model:page-size="store.supplierLimit"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="store.supplierTotal"
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
  const result = await store.getSuppliers()
  if (!result.success) ElMessage.error(result.message)
}

const handleReset = async () => {
  const result = await store.resetSupplierFilter()
  if (!result.success) ElMessage.error(result.message)
}

const handleSizeChange = async (size) => {
  const result = await store.handleSupplierSizeChange(size)
  if (!result.success) ElMessage.error(result.message)
}

const handleCurrentChange = async (current) => {
  const result = await store.handleSupplierCurrentChange(current)
  if (!result.success) ElMessage.error(result.message)
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该供应商吗？', '提示', { type: 'warning' })
    const result = await store.deleteSupplier(id)
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
.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
