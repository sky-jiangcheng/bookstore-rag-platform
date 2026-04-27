<template>
  <div class="book-management-container">
    <h2>图书管理</h2>
    
    <!-- 搜索表单 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="图书标题">
          <el-input v-model="searchForm.title" placeholder="请输入图书标题" clearable />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="searchForm.author" placeholder="请输入作者" clearable />
        </el-form-item>
        <el-form-item label="出版社">
          <el-input v-model="searchForm.publisher" placeholder="请输入出版社" clearable />
        </el-form-item>
        <el-form-item label="条码">
          <el-input v-model="searchForm.barcode" placeholder="请输入条码" clearable />
        </el-form-item>
        <el-form-item label="库存范围">
          <el-input-number v-model="searchForm.minStock" placeholder="最小" :min="0" style="width: 100px;" />
          <span style="margin: 0 10px;">-</span>
          <el-input-number v-model="searchForm.maxStock" placeholder="最大" :min="0" style="width: 100px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchBooks">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 图书列表 -->
    <el-card class="book-list-card">
      <template #header>
        <div class="card-header">
          <span>图书列表</span>
          <div class="header-actions">
            <el-button type="primary" @click="openAddBookDialog">
              <el-icon><Plus /></el-icon>
              新增图书
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        v-loading="loading"
        :data="bookList"
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
            <el-tag :type="getStockTagType(scope.row.stock)">
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
              <el-button size="small" @click="viewBookDetail(scope.row)">查看</el-button>
              <el-button type="primary" size="small" @click="openEditBookDialog(scope.row)">编辑</el-button>
              <el-button type="warning" size="small" @click="openUpdateStockDialog(scope.row)">
                调整库存
              </el-button>
              <el-button type="success" size="small" @click="addToPurchase(scope.row)">
                加入采购
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination" style="margin-top: 20px;">
        <el-pagination
          :current-page="pagination.currentPage"
          @update:current-page="val => pagination.currentPage = val"
          :page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 图书详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="图书详情" width="800px">
      <el-descriptions :column="2" border v-if="currentBook">
          <el-descriptions-item label="ID">{{ currentBook.id }}</el-descriptions-item>
          <el-descriptions-item label="条码">{{ currentBook.barcode }}</el-descriptions-item>
          <el-descriptions-item label="标题">{{ currentBook.title }}</el-descriptions-item>
          <el-descriptions-item label="作者">{{ currentBook.author }}</el-descriptions-item>
          <el-descriptions-item label="出版社">{{ currentBook.publisher }}</el-descriptions-item>
          <el-descriptions-item label="丛书">{{ currentBook.series || '-' }}</el-descriptions-item>
          <el-descriptions-item label="价格">¥{{ currentBook.price?.toFixed(2) || '0.00' }}</el-descriptions-item>
          <el-descriptions-item label="库存">
            <el-tag :type="getStockTagType(currentBook.stock)">
              {{ currentBook.stock }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="折扣">{{ Math.round((currentBook.discount || 0) * 100) }}%</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentBook.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentBook.updated_at }}</el-descriptions-item>
          <el-descriptions-item label="简介" :span="2">
            <el-popover placement="top" :width="600" trigger="hover">
              <template #reference>
                <span>{{ currentBook.summary ? (currentBook.summary.length > 100 ? currentBook.summary.substring(0, 100) + '...' : currentBook.summary) : '-' }}</span>
              </template>
              <pre>{{ currentBook.summary || '-' }}</pre>
            </el-popover>
          </el-descriptions-item>
        </el-descriptions>
    </el-dialog>
    
    <!-- 编辑图书对话框 -->
    <el-dialog v-model="editDialogVisible" :title="isAddMode ? '新增图书' : '编辑图书'" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="条码" required>
          <el-input v-model="editForm.barcode" placeholder="请输入条码" />
        </el-form-item>
        <el-form-item label="图书标题" required>
          <el-input v-model="editForm.title" placeholder="请输入图书标题" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="editForm.author" placeholder="请输入作者" />
        </el-form-item>
        <el-form-item label="出版社">
          <el-input v-model="editForm.publisher" placeholder="请输入出版社" />
        </el-form-item>
        <el-form-item label="丛书">
          <el-input v-model="editForm.series" placeholder="请输入丛书" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input v-model.number="editForm.price" type="number" placeholder="请输入价格" :min="0" step="0.01" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="editForm.stock" :min="0" placeholder="请输入库存" />
        </el-form-item>
        <el-form-item label="折扣">
          <el-input v-model.number="editForm.discount" type="number" placeholder="请输入折扣" :min="0" :max="1" step="0.01" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="editForm.summary" type="textarea" placeholder="请输入图书简介" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveBook">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 调整库存对话框 -->
    <el-dialog v-model="stockDialogVisible" title="调整库存" width="400px">
      <el-form :model="stockForm" label-width="80px">
        <el-form-item label="图书名称" disabled>
          <el-input v-model="stockForm.bookTitle" />
        </el-form-item>
        <el-form-item label="当前库存" disabled>
          <el-input v-model="stockForm.currentStock" />
        </el-form-item>
        <el-form-item label="新库存" required>
          <el-input-number v-model="stockForm.newStock" :min="0" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="stockDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateStock">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 采购列表 -->
    <el-card v-if="purchaseItems.length > 0" class="purchase-list-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>已选择采购书籍 ({{ purchaseItems.length }})</span>
          <div class="header-actions">
            <el-button @click="clearPurchaseItems">清空</el-button>
            <el-button type="success" @click="goToPurchase">
              前往采购
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="purchaseItems" style="width: 100%" border>
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
            <el-button type="danger" size="small" @click="removePurchaseItem(scope.$index)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { ElMessage } from 'element-plus'
import { Search, Plus, Edit, Remove, RefreshLeft } from '@element-plus/icons-vue'

// 搜索表单
const searchForm = reactive({
  title: '',
  author: '',
  publisher: '',
  barcode: '',
  minStock: null,
  maxStock: null
})

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 图书列表
const bookList = ref([])
const loading = ref(false)

// 对话框状态
const detailDialogVisible = ref(false)
const editDialogVisible = ref(false)
const stockDialogVisible = ref(false)

// 当前操作的图书
const currentBook = ref(null)
const isAddMode = ref(false)

// 编辑表单
const editForm = reactive({
  id: null,
  barcode: '',
  title: '',
  author: '',
  publisher: '',
  series: '',
  price: 0,
  stock: 0,
  discount: 0,
  summary: ''
})

// 库存调整表单
const stockForm = reactive({
  bookId: null,
  bookTitle: '',
  currentStock: 0,
  newStock: 0
})

// 多选数据
const multipleSelection = ref([])

// 路由
const router = useRouter()

// 采购列表
const purchaseItems = ref([])

// 获取图书列表
const getBooks = async () => {
  loading.value = true
  try {
    const params = {
      title: searchForm.title || undefined,
      author: searchForm.author || undefined,
      publisher: searchForm.publisher || undefined,
      barcode: searchForm.barcode || undefined,
      min_stock: searchForm.minStock !== null ? searchForm.minStock : undefined,
      max_stock: searchForm.maxStock !== null ? searchForm.maxStock : undefined,
      page: pagination.currentPage,
      limit: pagination.pageSize
    }
    
    const response = await request.get('/books', { params })
    bookList.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('获取图书列表失败:', error)
    ElMessage.error('获取图书列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索图书
const searchBooks = () => {
  pagination.currentPage = 1
  getBooks()
}

// 重置搜索
const resetSearch = () => {
  Object.assign(searchForm, {
    title: '',
    author: '',
    publisher: '',
    barcode: '',
    minStock: null,
    maxStock: null
  })
  pagination.currentPage = 1
  getBooks()
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.pageSize = size
  getBooks()
}

const handleCurrentChange = (current) => {
  pagination.currentPage = current
  getBooks()
}

// 多选处理
const handleSelectionChange = (val) => {
  multipleSelection.value = val
}

// 查看图书详情
const viewBookDetail = async (book) => {
  try {
    const response = await request.get(`/books/${book.id}`)
    currentBook.value = response.data
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取图书详情失败:', error)
    ElMessage.error('获取图书详情失败')
  }
}

// 打开编辑对话框
const openEditBookDialog = (book) => {
  isAddMode.value = false
  Object.assign(editForm, {
    id: book.id,
    barcode: book.barcode,
    title: book.title,
    author: book.author,
    publisher: book.publisher,
    series: book.series || '',
    price: book.price || 0,
    stock: book.stock,
    discount: book.discount || 0,
    summary: book.summary || ''
  })
  editDialogVisible.value = true
}

// 打开新增对话框
const openAddBookDialog = () => {
  isAddMode.value = true
  Object.assign(editForm, {
    id: null,
    barcode: '',
    title: '',
    author: '',
    publisher: '',
    series: '',
    price: 0,
    stock: 0,
    discount: 0,
    summary: ''
  })
  editDialogVisible.value = true
}

// 保存图书
const saveBook = async () => {
  if (!editForm.title || !editForm.barcode) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  try {
    if (isAddMode.value) {
      // 新增图书
      // 这里需要实现新增图书的API调用
      ElMessage.success('新增图书功能开发中')
    } else {
      // 更新图书
      await request.put(`/books/${editForm.id}`, editForm)
      ElMessage.success('图书信息更新成功')
      getBooks()
    }
    editDialogVisible.value = false
  } catch (error) {
    console.error('保存图书失败:', error)
    ElMessage.error('保存图书失败')
  }
}

// 打开库存调整对话框
const openUpdateStockDialog = (book) => {
  Object.assign(stockForm, {
    bookId: book.id,
    bookTitle: book.title,
    currentStock: book.stock,
    newStock: book.stock
  })
  stockDialogVisible.value = true
}

// 更新库存
const updateStock = async () => {
  try {
    await request.put(`/books/${stockForm.bookId}/stock`, {
      stock: stockForm.newStock
    })
    ElMessage.success('库存更新成功')
    getBooks()
    stockDialogVisible.value = false
  } catch (error) {
    console.error('更新库存失败:', error)
    ElMessage.error('更新库存失败')
  }
}

// 获取库存标签类型
const getStockTagType = (stock) => {
  if (stock === 0) return 'danger'
  if (stock < 10) return 'warning'
  return 'success'
}

// 加入采购
const addToPurchase = (book) => {
  // 检查书籍是否已在采购列表中
  const existingItem = purchaseItems.value.find(item => item.book_id === book.id)
  if (existingItem) {
    ElMessage.warning('该书籍已在采购列表中')
    return
  }
  
  // 添加到采购列表
  purchaseItems.value.push({
    book_id: book.id,
    title: book.title,
    author: book.author,
    quantity: 1,
    unit_price: book.price || 0
  })
  
  ElMessage.success(`已加入采购：${book.title}`)
}

// 前往采购页面
const goToPurchase = () => {
  // 存储采购物品到sessionStorage
  sessionStorage.setItem('purchaseItems', JSON.stringify(purchaseItems.value))
  
  // 跳转到采购页面
  router.push('/purchase')
}

// 清空采购列表
const clearPurchaseItems = () => {
  purchaseItems.value = []
  sessionStorage.removeItem('purchaseItems')
  ElMessage.info('已清空采购列表')
}

// 移除采购物品
const removePurchaseItem = (index) => {
  purchaseItems.value.splice(index, 1)
  ElMessage.success('已移除采购物品')
}

// 初始化
onMounted(() => {
  getBooks()
})
</script>

<style scoped>
.book-management-container {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.search-form {
  margin-bottom: 10px;
}

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

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .search-form {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .search-form .el-form-item {
    margin-bottom: 10px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 5px;
  }
  
  .action-buttons .el-button {
    width: 100%;
  }
}
</style>
