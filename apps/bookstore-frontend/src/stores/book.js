import { defineStore } from 'pinia'
import { bookApi } from '@/api'

/**
 * 图书管理Store
 */
export const useBookStore = defineStore('book', {
  state: () => ({
    // 搜索表单
    searchForm: {
      title: '',
      author: '',
      publisher: '',
      barcode: '',
      minStock: null,
      maxStock: null
    },
    
    // 分页信息
    pagination: {
      currentPage: 1,
      pageSize: 20,
      total: 0
    },
    
    // 图书列表
    bookList: [],
    loading: false,
    
    // 当前操作的图书
    currentBook: null,
    
    // 多选数据
    multipleSelection: [],
    
    // 采购列表
    purchaseItems: [],
    
    // 对话框状态
    detailDialogVisible: false,
    editDialogVisible: false,
    stockDialogVisible: false,
    isAddMode: false,
    
    // 编辑表单
    editForm: {
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
    },
    
    // 库存调整表单
    stockForm: {
      bookId: null,
      bookTitle: '',
      currentStock: 0,
      newStock: 0
    }
  }),

  getters: {
    // 是否有选中的图书
    hasSelection: (state) => state.multipleSelection.length > 0,
    
    // 是否有采购项
    hasPurchaseItems: (state) => state.purchaseItems.length > 0,
    
    // 采购总价
    purchaseTotalPrice: (state) => {
      return state.purchaseItems.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0)
    }
  },

  actions: {
    // 获取图书列表
    async getBooks() {
      this.loading = true
      try {
        const params = {
          title: this.searchForm.title || undefined,
          author: this.searchForm.author || undefined,
          publisher: this.searchForm.publisher || undefined,
          barcode: this.searchForm.barcode || undefined,
          min_stock: this.searchForm.minStock !== null ? this.searchForm.minStock : undefined,
          max_stock: this.searchForm.maxStock !== null ? this.searchForm.maxStock : undefined,
          page: this.pagination.currentPage,
          limit: this.pagination.pageSize
        }
        
        const response = await bookApi.getList(params)
        this.bookList = response.data.items
        this.pagination.total = response.data.total
        return { success: true }
      } catch (error) {
        console.error('获取图书列表失败:', error)
        return { success: false, message: '获取图书列表失败' }
      } finally {
        this.loading = false
      }
    },

    // 搜索图书
    async searchBooks() {
      this.pagination.currentPage = 1
      return await this.getBooks()
    },

    // 重置搜索
    async resetSearch() {
      this.searchForm = {
        title: '',
        author: '',
        publisher: '',
        barcode: '',
        minStock: null,
        maxStock: null
      }
      this.pagination.currentPage = 1
      return await this.getBooks()
    },

    // 分页处理
    async handleSizeChange(size) {
      this.pagination.pageSize = size
      return await this.getBooks()
    },

    async handleCurrentChange(current) {
      this.pagination.currentPage = current
      return await this.getBooks()
    },

    // 多选处理
    handleSelectionChange(val) {
      this.multipleSelection = val
    },

    // 查看图书详情
    async viewBookDetail(book) {
      try {
        const response = await bookApi.getDetail(book.id)
        this.currentBook = response.data
        this.detailDialogVisible = true
        return { success: true }
      } catch (error) {
        console.error('获取图书详情失败:', error)
        return { success: false, message: '获取图书详情失败' }
      }
    },

    // 打开编辑对话框
    openEditBookDialog(book) {
      this.isAddMode = false
      this.editForm = {
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
      }
      this.editDialogVisible = true
    },

    // 打开新增对话框
    openAddBookDialog() {
      this.isAddMode = true
      this.editForm = {
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
      }
      this.editDialogVisible = true
    },

    // 保存图书
    async saveBook() {
      if (!this.editForm.title || !this.editForm.barcode) {
        return { success: false, message: '请填写必填项' }
      }
      
      try {
        if (this.isAddMode) {
          // 新增图书
          return { success: false, message: '新增图书功能开发中' }
        } else {
          // 更新图书
          await bookApi.update(this.editForm.id, this.editForm)
          await this.getBooks()
          this.editDialogVisible = false
          return { success: true, message: '图书信息更新成功' }
        }
      } catch (error) {
        console.error('保存图书失败:', error)
        return { success: false, message: '保存图书失败' }
      }
    },

    // 打开库存调整对话框
    openUpdateStockDialog(book) {
      this.stockForm = {
        bookId: book.id,
        bookTitle: book.title,
        currentStock: book.stock,
        newStock: book.stock
      }
      this.stockDialogVisible = true
    },

    // 更新库存
    async updateStock() {
      try {
        await bookApi.updateStock(this.stockForm.bookId, {
          stock: this.stockForm.newStock
        })
        await this.getBooks()
        this.stockDialogVisible = false
        return { success: true, message: '库存更新成功' }
      } catch (error) {
        console.error('更新库存失败:', error)
        return { success: false, message: '更新库存失败' }
      }
    },

    // 获取库存标签类型
    getStockTagType(stock) {
      if (stock === 0) return 'danger'
      if (stock < 10) return 'warning'
      return 'success'
    },

    // 加入采购
    addToPurchase(book) {
      // 检查书籍是否已在采购列表中
      const existingItem = this.purchaseItems.find(item => item.book_id === book.id)
      if (existingItem) {
        return { success: false, message: '该书籍已在采购列表中' }
      }
      
      // 添加到采购列表
      this.purchaseItems.push({
        book_id: book.id,
        title: book.title,
        author: book.author,
        quantity: 1,
        unit_price: book.price || 0
      })
      
      return { success: true, message: `已加入采购：${book.title}` }
    },

    // 移除采购物品
    removePurchaseItem(index) {
      this.purchaseItems.splice(index, 1)
      return { success: true, message: '已移除采购物品' }
    },

    // 清空采购列表
    clearPurchaseItems() {
      this.purchaseItems = []
      return { success: true, message: '已清空采购列表' }
    }
  }
})
