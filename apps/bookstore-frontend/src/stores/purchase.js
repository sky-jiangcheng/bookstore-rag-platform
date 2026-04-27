import { defineStore } from 'pinia'
import request from '@/utils/request'

export const usePurchaseStore = defineStore('purchase', {
  state: () => ({
    // Tab状态
    activeTab: 'suppliers',
    
    // 供应商管理
    supplierData: [],
    supplierLoading: false,
    supplierTotal: 0,
    supplierPage: 1,
    supplierLimit: 20,
    supplierFilter: {
      name: ''
    },
    supplierDialogVisible: false,
    supplierDialogTitle: '新增供应商',
    supplierForm: {
      id: null,
      name: '',
      contact_person: '',
      phone: '',
      email: '',
      address: '',
      tax_number: '',
      bank_account: '',
      remark: ''
    },
    supplierOptions: [],
    
    // 采购单管理
    purchaseData: [],
    purchaseLoading: false,
    purchaseTotal: 0,
    purchasePage: 1,
    purchaseLimit: 20,
    purchaseFilter: {
      order_number: '',
      supplier_id: '',
      status: ''
    },
    purchaseDialogVisible: false,
    purchaseDetailVisible: false,
    statusDialogVisible: false,
    purchaseForm: {
      supplier_id: '',
      expected_delivery_date: '',
      remark: '',
      items: []
    },
    currentPurchaseOrder: null,
    statusForm: {
      order_id: null,
      order_number: '',
      current_status: '',
      new_status: ''
    },
    
    // 书籍选项
    bookOptions: []
  }),

  getters: {
    supplierPagination: (state) => ({
      currentPage: state.supplierPage,
      pageSize: state.supplierLimit,
      total: state.supplierTotal
    }),
    purchasePagination: (state) => ({
      currentPage: state.purchasePage,
      pageSize: state.purchaseLimit,
      total: state.purchaseTotal
    })
  },

  actions: {
    // 获取供应商列表
    async getSuppliers() {
      this.supplierLoading = true
      try {
        const params = {
          page: this.supplierPage,
          limit: this.supplierLimit,
          name: this.supplierFilter.name || undefined
        }
        const response = await request.get('/purchase/suppliers', { params })
        this.supplierData = response.data.items
        this.supplierTotal = response.data.total
        return { success: true }
      } catch (error) {
        console.error('获取供应商列表失败:', error)
        return { success: false, message: '获取供应商列表失败' }
      } finally {
        this.supplierLoading = false
      }
    },

    // 获取采购单列表
    async getPurchaseOrders() {
      this.purchaseLoading = true
      try {
        const params = {
          page: this.purchasePage,
          limit: this.purchaseLimit,
          order_number: this.purchaseFilter.order_number || undefined,
          supplier_id: this.purchaseFilter.supplier_id || undefined,
          status: this.purchaseFilter.status || undefined
        }
        const response = await request.get('/purchase/orders', { params })
        this.purchaseData = response.data.items
        this.purchaseTotal = response.data.total
        return { success: true }
      } catch (error) {
        console.error('获取采购单列表失败:', error)
        return { success: false, message: '获取采购单列表失败' }
      } finally {
        this.purchaseLoading = false
      }
    },

    // 获取供应商选项
    async getSupplierOptions() {
      try {
        const response = await request.get('/purchase/suppliers', { params: { limit: 1000 } })
        this.supplierOptions = response.data.items
        return { success: true }
      } catch (error) {
        console.error('获取供应商选项失败:', error)
        return { success: false, message: '获取供应商选项失败' }
      }
    },

    // 获取书籍选项
    async getBookOptions() {
      try {
        const response = await request.get('/purchase/books', { params: { limit: 100 } })
        this.bookOptions = response.data.items
        return { success: true }
      } catch (error) {
        console.error('获取书籍选项失败:', error)
        return { success: false, message: '获取书籍选项失败' }
      }
    },

    // 供应商分页
    async handleSupplierSizeChange(size) {
      this.supplierLimit = size
      return await this.getSuppliers()
    },

    async handleSupplierCurrentChange(current) {
      this.supplierPage = current
      return await this.getSuppliers()
    },

    // 采购单分页
    async handlePurchaseSizeChange(size) {
      this.purchaseLimit = size
      return await this.getPurchaseOrders()
    },

    async handlePurchaseCurrentChange(current) {
      this.purchasePage = current
      return await this.getPurchaseOrders()
    },

    // 重置供应商筛选
    async resetSupplierFilter() {
      this.supplierFilter.name = ''
      this.supplierPage = 1
      return await this.getSuppliers()
    },

    // 重置采购单筛选
    async resetPurchaseFilter() {
      this.purchaseFilter = {
        order_number: '',
        supplier_id: '',
        status: ''
      }
      this.purchasePage = 1
      return await this.getPurchaseOrders()
    },

    // 打开新增供应商对话框
    openAddSupplierDialog() {
      this.supplierDialogTitle = '新增供应商'
      this.supplierForm = {
        id: null,
        name: '',
        contact_person: '',
        phone: '',
        email: '',
        address: '',
        tax_number: '',
        bank_account: '',
        remark: ''
      }
      this.supplierDialogVisible = true
    },

    // 打开编辑供应商对话框
    openEditSupplierDialog(supplier) {
      this.supplierDialogTitle = '编辑供应商'
      this.supplierForm = { ...supplier }
      this.supplierDialogVisible = true
    },

    // 保存供应商
    async saveSupplier() {
      try {
        if (this.supplierForm.id) {
          await request.put(`/purchase/suppliers/${this.supplierForm.id}`, this.supplierForm)
        } else {
          await request.post('/purchase/suppliers', this.supplierForm)
        }
        this.supplierDialogVisible = false
        await this.getSuppliers()
        await this.getSupplierOptions()
        return { success: true, message: this.supplierForm.id ? '更新供应商成功' : '新增供应商成功' }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '保存失败' }
      }
    },

    // 删除供应商
    async deleteSupplier(supplierId) {
      try {
        await request.delete(`/purchase/suppliers/${supplierId}`)
        await this.getSuppliers()
        return { success: true, message: '删除供应商成功' }
      } catch (error) {
        return { success: false, message: '删除供应商失败' }
      }
    },

    // 打开新增采购单对话框
    openAddPurchaseOrderDialog() {
      this.purchaseForm = {
        supplier_id: '',
        expected_delivery_date: '',
        remark: '',
        items: []
      }
      this.purchaseDialogVisible = true
    },

    // 添加采购明细
    addPurchaseItem() {
      this.purchaseForm.items.push({
        book_id: '',
        quantity: 1,
        unit_price: 0
      })
    },

    // 移除采购明细
    removePurchaseItem(index) {
      this.purchaseForm.items.splice(index, 1)
    },

    // 保存采购单
    async savePurchaseOrder() {
      try {
        await request.post('/purchase/orders', this.purchaseForm)
        this.purchaseDialogVisible = false
        await this.getPurchaseOrders()
        return { success: true, message: '新增采购单成功' }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '保存失败' }
      }
    },

    // 查看采购单详情
    viewPurchaseOrder(order) {
      this.currentPurchaseOrder = order
      this.purchaseDetailVisible = true
    },

    // 打开更新订单状态对话框
    updateOrderStatus(order) {
      this.statusForm = {
        order_id: order.id,
        order_number: order.order_number,
        current_status: order.status,
        new_status: ''
      }
      this.statusDialogVisible = true
    },

    // 保存订单状态
    async saveOrderStatus() {
      try {
        await request.put(`/purchase/orders/${this.statusForm.order_id}/status`, {
          status: this.statusForm.new_status
        })
        this.statusDialogVisible = false
        await this.getPurchaseOrders()
        return { success: true, message: '更新订单状态成功' }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || '更新失败' }
      }
    },

    // 删除采购单
    async deletePurchaseOrder(orderId) {
      try {
        await request.delete(`/purchase/orders/${orderId}`)
        await this.getPurchaseOrders()
        return { success: true, message: '删除采购单成功' }
      } catch (error) {
        return { success: false, message: '删除采购单失败' }
      }
    },

    // 获取状态标签类型
    getStatusTagType(status) {
      const typeMap = {
        'PENDING': 'info',
        'APPROVED': 'warning',
        'ORDERED': 'primary',
        'DELIVERED': 'success',
        'COMPLETED': 'success',
        'CANCELLED': 'danger'
      }
      return typeMap[status] || 'info'
    },

    // 获取状态标签文本
    getStatusLabel(status) {
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
  }
})
