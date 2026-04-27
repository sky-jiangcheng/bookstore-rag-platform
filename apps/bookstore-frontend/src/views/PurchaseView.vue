<template>
  <div class="purchase-container">
    <h2>采购管理</h2>
    
    <el-tabs v-model="activeTab">
      <!-- 供应商管理 -->
      <el-tab-pane label="供应商管理" name="suppliers">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>供应商列表</span>
              <el-button type="primary" @click="openAddSupplierDialog">
                <el-icon><Plus /></el-icon>
                新增供应商
              </el-button>
            </div>
          </template>
          
          <!-- 筛选表单 -->
          <el-form :inline="true" :model="supplierFilter" class="filter-form" style="margin-bottom: 20px;">
            <el-form-item label="供应商名称">
              <el-input v-model="supplierFilter.name" placeholder="请输入供应商名称" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="getSuppliers">查询</el-button>
              <el-button @click="resetSupplierFilter">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 供应商表格 -->
          <el-table
            v-loading="supplierLoading"
            :data="supplierData"
            style="width: 100%"
            border
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="供应商名称" min-width="150" />
            <el-table-column prop="contact_person" label="联系人" width="120" />
            <el-table-column prop="phone" label="联系电话" width="150" />
            <el-table-column prop="email" label="邮箱" width="180" />
            <el-table-column prop="address" label="地址" min-width="200" />
            <el-table-column prop="create_time" label="创建时间" width="180" />
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button type="primary" size="small" @click="openEditSupplierDialog(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteSupplier(scope.row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination" style="margin-top: 20px;">
            <el-pagination
              v-model:current-page="supplierPage"
              v-model:page-size="supplierLimit"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="supplierTotal"
              @size-change="handleSupplierSizeChange"
              @current-change="handleSupplierCurrentChange"
            />
          </div>
        </el-card>
      </el-tab-pane>
      
      <!-- 采购单管理 -->
      <el-tab-pane label="采购单管理" name="purchaseOrders">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>采购单列表</span>
              <el-button type="primary" @click="openAddPurchaseOrderDialog">
                <el-icon><Plus /></el-icon>
                新增采购单
              </el-button>
            </div>
          </template>
          
          <!-- 筛选表单 -->
          <el-form :inline="true" :model="purchaseFilter" class="filter-form" style="margin-bottom: 20px;">
            <el-form-item label="订单编号">
              <el-input v-model="purchaseFilter.order_number" placeholder="请输入订单编号" clearable />
            </el-form-item>
            <el-form-item label="供应商">
              <el-select v-model="purchaseFilter.supplier_id" placeholder="请选择供应商" clearable>
                <el-option
                  v-for="supplier in supplierOptions"
                  :key="supplier.id"
                  :label="supplier.name"
                  :value="supplier.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="订单状态">
              <el-select v-model="purchaseFilter.status" placeholder="请选择订单状态" clearable>
                <el-option label="待处理" value="PENDING" />
                <el-option label="已批准" value="APPROVED" />
                <el-option label="已下单" value="ORDERED" />
                <el-option label="已送达" value="DELIVERED" />
                <el-option label="已完成" value="COMPLETED" />
                <el-option label="已取消" value="CANCELLED" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="getPurchaseOrders">查询</el-button>
              <el-button @click="resetPurchaseFilter">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 采购单表格 -->
          <el-table
            v-loading="purchaseLoading"
            :data="purchaseData"
            style="width: 100%"
            border
          >
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
                <el-tag :type="getStatusTagType(scope.row.status)">
                  {{ getStatusLabel(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="order_date" label="下单日期" width="180" />
            <el-table-column prop="expected_delivery_date" label="预计送达" width="180" />
            <el-table-column prop="actual_delivery_date" label="实际送达" width="180" />
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button size="small" @click="viewPurchaseOrder(scope.row)">查看</el-button>
                <el-button size="small" type="primary" @click="updateOrderStatus(scope.row)">
                  更新状态
                </el-button>
                <el-button size="small" type="danger" @click="deletePurchaseOrder(scope.row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination" style="margin-top: 20px;">
            <el-pagination
              v-model:current-page="purchasePage"
              v-model:page-size="purchaseLimit"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="purchaseTotal"
              @size-change="handlePurchaseSizeChange"
              @current-change="handlePurchaseCurrentChange"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 新增/编辑供应商对话框 -->
    <el-dialog v-model="supplierDialogVisible" :title="supplierDialogTitle" width="600px">
      <el-form :model="supplierForm" label-width="100px">
        <el-form-item label="供应商名称" required>
          <el-input v-model="supplierForm.name" placeholder="请输入供应商名称" />
        </el-form-item>
        <el-form-item label="联系人" required>
          <el-input v-model="supplierForm.contact_person" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="supplierForm.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="supplierForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="supplierForm.address" placeholder="请输入地址" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="税号">
          <el-input v-model="supplierForm.tax_number" placeholder="请输入税号" />
        </el-form-item>
        <el-form-item label="银行账号">
          <el-input v-model="supplierForm.bank_account" placeholder="请输入银行账号" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="supplierForm.remark" placeholder="请输入备注" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="supplierDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveSupplier">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 新增采购单对话框 -->
    <el-dialog v-model="purchaseDialogVisible" title="新增采购单" width="800px">
      <el-form :model="purchaseForm" label-width="100px">
        <el-form-item label="供应商" required>
          <el-select v-model="purchaseForm.supplier_id" placeholder="请选择供应商" style="width: 100%;">
            <el-option
              v-for="supplier in supplierOptions"
              :key="supplier.id"
              :label="supplier.name"
              :value="supplier.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预计送达日期">
          <el-date-picker
            v-model="purchaseForm.expected_delivery_date"
            type="datetime"
            placeholder="选择预计送达日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="purchaseForm.remark" placeholder="请输入备注" type="textarea" :rows="3" />
        </el-form-item>
        
        <!-- 采购明细 -->
        <el-form-item label="采购明细" required>
          <el-button type="primary" @click="addPurchaseItem" style="margin-bottom: 10px;">
            <el-icon><Plus /></el-icon>
            新增明细
          </el-button>
          
          <el-table :data="purchaseForm.items" border style="width: 100%;">
            <el-table-column label="书籍" width="300">
              <template #default="scope">
                <el-select v-model="scope.row.book_id" placeholder="请选择书籍" style="width: 100%;">
                  <el-option
                    v-for="book in bookOptions"
                    :key="book.id"
                    :label="book.title"
                    :value="book.id"
                  />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="数量" width="120">
              <template #default="scope">
                <el-input-number v-model="scope.row.quantity" :min="1" />
              </template>
            </el-table-column>
            <el-table-column label="单价" width="120">
              <template #default="scope">
                <el-input v-model.number="scope.row.unit_price" type="number" :min="0" step="0.01" />
              </template>
            </el-table-column>
            <el-table-column label="金额" width="120">
              <template #default="scope">
                <span>{{ (scope.row.quantity * scope.row.unit_price).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="scope">
                <el-button type="danger" size="small" @click="removePurchaseItem(scope.$index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="purchaseDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePurchaseOrder">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 采购单详情对话框 -->
    <el-dialog v-model="purchaseDetailVisible" title="采购单详情" width="800px">
      <div v-if="currentPurchaseOrder">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单编号">{{ currentPurchaseOrder.order_number }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ currentPurchaseOrder.supplier_name }}</el-descriptions-item>
          <el-descriptions-item label="总金额">{{ currentPurchaseOrder.total_amount.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="getStatusTagType(currentPurchaseOrder.status)">
              {{ getStatusLabel(currentPurchaseOrder.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下单日期">{{ currentPurchaseOrder.order_date }}</el-descriptions-item>
          <el-descriptions-item label="预计送达">{{ currentPurchaseOrder.expected_delivery_date }}</el-descriptions-item>
          <el-descriptions-item label="实际送达">{{ currentPurchaseOrder.actual_delivery_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ currentPurchaseOrder.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
        
        <h3 style="margin-top: 20px;">采购明细</h3>
        <el-table :data="currentPurchaseOrder.items" border style="width: 100%;">
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
    
    <!-- 更新订单状态对话框 -->
    <el-dialog v-model="statusDialogVisible" title="更新订单状态" width="400px">
      <el-form :model="statusForm" label-width="100px">
        <el-form-item label="订单编号">
          <el-input v-model="statusForm.order_number" disabled />
        </el-form-item>
        <el-form-item label="当前状态">
          <el-input v-model="statusForm.current_status" disabled />
        </el-form-item>
        <el-form-item label="新状态" required>
          <el-select v-model="statusForm.new_status" placeholder="请选择新状态" style="width: 100%;">
            <el-option label="待处理" value="PENDING" />
            <el-option label="已批准" value="APPROVED" />
            <el-option label="已下单" value="ORDERED" />
            <el-option label="已送达" value="DELIVERED" />
            <el-option label="已完成" value="COMPLETED" />
            <el-option label="已取消" value="CANCELLED" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="statusDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveOrderStatus">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import request from '../utils/request'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

// 标签页
const activeTab = ref('suppliers')

// 供应商管理
const supplierData = ref([])
const supplierLoading = ref(false)
const supplierTotal = ref(0)
const supplierPage = ref(1)
const supplierLimit = ref(20)
const supplierFilter = reactive({
  name: ''
})
const supplierDialogVisible = ref(false)
const supplierDialogTitle = ref('新增供应商')
const supplierForm = reactive({
  id: null,
  name: '',
  contact_person: '',
  phone: '',
  email: '',
  address: '',
  tax_number: '',
  bank_account: '',
  remark: ''
})
const supplierOptions = ref([])

// 采购单管理
const purchaseData = ref([])
const purchaseLoading = ref(false)
const purchaseTotal = ref(0)
const purchasePage = ref(1)
const purchaseLimit = ref(20)
const purchaseFilter = reactive({
  order_number: '',
  supplier_id: '',
  status: ''
})
const purchaseDialogVisible = ref(false)
const purchaseDetailVisible = ref(false)
const statusDialogVisible = ref(false)
const purchaseForm = reactive({
  supplier_id: '',
  expected_delivery_date: '',
  remark: '',
  items: []
})
const currentPurchaseOrder = ref(null)
const statusForm = reactive({
  order_id: null,
  order_number: '',
  current_status: '',
  new_status: ''
})

// 书籍选项
const bookOptions = ref([])

// 获取供应商列表
const getSuppliers = async () => {
  supplierLoading.value = true
  try {
    const params = {
      page: supplierPage.value,
      limit: supplierLimit.value,
      name: supplierFilter.name || undefined
    }
    
    const response = await request.get('/purchase/suppliers', { params })
    supplierData.value = response.data.items
    supplierTotal.value = response.data.total
  } catch (error) {
    console.error('获取供应商列表失败:', error)
    ElMessage.error('获取供应商列表失败')
  } finally {
    supplierLoading.value = false
  }
}

// 获取采购单列表
const getPurchaseOrders = async () => {
  purchaseLoading.value = true
  try {
    const params = {
      page: purchasePage.value,
      limit: purchaseLimit.value,
      order_number: purchaseFilter.order_number || undefined,
      supplier_id: purchaseFilter.supplier_id || undefined,
      status: purchaseFilter.status || undefined
    }
    
    const response = await request.get('/purchase/orders', { params })
    purchaseData.value = response.data.items
    purchaseTotal.value = response.data.total
  } catch (error) {
    console.error('获取采购单列表失败:', error)
    ElMessage.error('获取采购单列表失败')
  } finally {
    purchaseLoading.value = false
  }
}

// 获取供应商选项
const getSupplierOptions = async () => {
  try {
    const response = await request.get('/purchase/suppliers', { params: { limit: 1000 } })
    supplierOptions.value = response.data.items
  } catch (error) {
    console.error('获取供应商选项失败:', error)
  }
}

// 获取书籍选项
const getBookOptions = async () => {
  try {
    const response = await request.get('/purchase/books', { params: { limit: 100 } })
    bookOptions.value = response.data.items
  } catch (error) {
    console.error('获取书籍选项失败:', error)
  }
}

// 打开新增供应商对话框
const openAddSupplierDialog = () => {
  supplierDialogTitle.value = '新增供应商'
  Object.assign(supplierForm, {
    id: null,
    name: '',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    tax_number: '',
    bank_account: '',
    remark: ''
  })
  supplierDialogVisible.value = true
}

// 打开编辑供应商对话框
const openEditSupplierDialog = (supplier) => {
  supplierDialogTitle.value = '编辑供应商'
  Object.assign(supplierForm, {
    id: supplier.id,
    name: supplier.name,
    contact_person: supplier.contact_person,
    phone: supplier.phone,
    email: supplier.email,
    address: supplier.address,
    tax_number: supplier.tax_number,
    bank_account: supplier.bank_account,
    remark: supplier.remark
  })
  supplierDialogVisible.value = true
}

// 保存供应商
const saveSupplier = async () => {
  if (!supplierForm.name || !supplierForm.contact_person || !supplierForm.phone) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  try {
    if (supplierForm.id) {
      // 更新
      await request.put(`/purchase/suppliers/${supplierForm.id}`, supplierForm)
      ElMessage.success('供应商更新成功')
    } else {
      // 新增
      await request.post('/purchase/suppliers', supplierForm)
      ElMessage.success('供应商新增成功')
    }
    
    supplierDialogVisible.value = false
    getSuppliers()
    getSupplierOptions()
  } catch (error) {
    console.error('保存供应商失败:', error)
    ElMessage.error('保存供应商失败')
  }
}

// 删除供应商
const deleteSupplier = async (id) => {
  try {
    await request.delete(`/purchase/suppliers/${id}`)
    ElMessage.success('供应商删除成功')
    getSuppliers()
    getSupplierOptions()
  } catch (error) {
    console.error('删除供应商失败:', error)
    ElMessage.error('删除供应商失败')
  }
}

// 打开新增采购单对话框
const openAddPurchaseOrderDialog = () => {
  // 检查sessionStorage中是否有采购物品
  const storedItems = sessionStorage.getItem('purchaseItems')
  let initialItems = []
  
  if (storedItems) {
    try {
      const items = JSON.parse(storedItems)
      initialItems = items.map(item => ({
        book_id: item.book_id,
        quantity: item.quantity,
        unit_price: item.unit_price,
        remark: ''
      }))
      // 清空sessionStorage
      sessionStorage.removeItem('purchaseItems')
    } catch (error) {
      console.error('解析采购物品失败:', error)
    }
  }
  
  Object.assign(purchaseForm, {
    supplier_id: '',
    expected_delivery_date: '',
    remark: '',
    items: initialItems
  })
  purchaseDialogVisible.value = true
}

// 添加采购明细
const addPurchaseItem = () => {
  purchaseForm.items.push({
    book_id: '',
    quantity: 1,
    unit_price: 0,
    remark: ''
  })
}

// 移除采购明细
const removePurchaseItem = (index) => {
  purchaseForm.items.splice(index, 1)
}

// 保存采购单
const savePurchaseOrder = async () => {
  if (!purchaseForm.supplier_id) {
    ElMessage.warning('请选择供应商')
    return
  }
  
  if (purchaseForm.items.length === 0) {
    ElMessage.warning('请添加采购明细')
    return
  }
  
  try {
    await request.post('/purchase/orders', purchaseForm)
    ElMessage.success('采购单创建成功')
    purchaseDialogVisible.value = false
    getPurchaseOrders()
  } catch (error) {
    console.error('保存采购单失败:', error)
    ElMessage.error('保存采购单失败')
  }
}

// 查看采购单详情
const viewPurchaseOrder = async (order) => {
  try {
    const response = await request.get(`/purchase/orders/${order.id}`)
    currentPurchaseOrder.value = response.data
    purchaseDetailVisible.value = true
  } catch (error) {
    console.error('获取采购单详情失败:', error)
    ElMessage.error('获取采购单详情失败')
  }
}

// 更新订单状态
const updateOrderStatus = (order) => {
  Object.assign(statusForm, {
    order_id: order.id,
    order_number: order.order_number,
    current_status: getStatusLabel(order.status),
    new_status: order.status
  })
  statusDialogVisible.value = true
}

// 保存订单状态
const saveOrderStatus = async () => {
  try {
    await request.put(`/purchase/orders/${statusForm.order_id}/status`, {
      status: statusForm.new_status
    })
    ElMessage.success('订单状态更新成功')
    statusDialogVisible.value = false
    getPurchaseOrders()
  } catch (error) {
    console.error('更新订单状态失败:', error)
    ElMessage.error('更新订单状态失败')
  }
}

// 删除采购单
const deletePurchaseOrder = async (id) => {
  try {
    await request.delete(`/purchase/orders/${id}`)
    ElMessage.success('采购单删除成功')
    getPurchaseOrders()
  } catch (error) {
    console.error('删除采购单失败:', error)
    ElMessage.error('删除采购单失败')
  }
}

// 重置供应商筛选
const resetSupplierFilter = () => {
  supplierFilter.name = ''
  getSuppliers()
}

// 重置采购单筛选
const resetPurchaseFilter = () => {
  purchaseFilter.order_number = ''
  purchaseFilter.supplier_id = ''
  purchaseFilter.status = ''
  getPurchaseOrders()
}

// 分页处理
const handleSupplierSizeChange = (size) => {
  supplierLimit.value = size
  getSuppliers()
}

const handleSupplierCurrentChange = (current) => {
  supplierPage.value = current
  getSuppliers()
}

const handlePurchaseSizeChange = (size) => {
  purchaseLimit.value = size
  getPurchaseOrders()
}

const handlePurchaseCurrentChange = (current) => {
  purchasePage.value = current
  getPurchaseOrders()
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  const typeMap = {
    'PENDING': 'info',
    'APPROVED': 'warning',
    'ORDERED': 'primary',
    'DELIVERED': 'success',
    'COMPLETED': 'success',
    'CANCELLED': 'danger'
  }
  return typeMap[status] || 'default'
}

// 获取状态标签
const getStatusLabel = (status) => {
  const labelMap = {
    'PENDING': '待处理',
    'APPROVED': '已批准',
    'ORDERED': '已下单',
    'DELIVERED': '已送达',
    'COMPLETED': '已完成',
    'CANCELLED': '已取消'
  }
  return labelMap[status] || status
}

// 初始化数据
onMounted(() => {
  getSuppliers()
  getSupplierOptions()
  getPurchaseOrders()
  getBookOptions()
})
</script>

<style scoped>
.purchase-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}

.amount {
  font-weight: bold;
  color: #409EFF;
}

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
}
</style>