import { defineStore } from 'pinia'
import request from '@/utils/request'

export const useFilterStore = defineStore('filter', {
  state: () => ({
    // 类别管理
    categories: [],
    currentCategory: null,
    categorySearchQuery: '',
    
    // 分页相关
    currentPage: 1,
    pageSize: 10,
    totalCategories: 0,
    
    // 关键词管理
    keywords: [],
    keywordSearchQuery: '',
    
    // 对话框状态
    keywordDialogVisible: false,
    addCategoryDialogVisible: false,
    editCategoryDialogVisible: false,
    addKeywordDialogVisible: false,
    batchKeywordDialogVisible: false,
    importDialogVisible: false,
    
    // 表单数据
    categoryForm: {
      id: null,
      name: '',
      description: '',
      is_active: 1
    },
    keywordForm: {
      id: null,
      keyword: '',
      is_active: 1
    },
    batchKeywords: '',
    importContent: ''
  }),

  getters: {
    hasCategories: (state) => state.categories.length > 0,
    hasKeywords: (state) => state.keywords.length > 0,
    filteredCategories: (state) => {
      if (!state.categorySearchQuery) {
        return state.categories
      }
      return state.categories.filter(category => 
        category.name.toLowerCase().includes(state.categorySearchQuery.toLowerCase())
      )
    }
  },

  actions: {
    // 加载类别列表
    async loadCategories() {
      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize
        }
        if (this.categorySearchQuery) {
          params.name = this.categorySearchQuery
        }
        const response = await request.get('/filters/categories', { params })
        this.categories = response.data.items || response.data
        this.totalCategories = response.data.total || this.categories.length
        return { success: true }
      } catch (error) {
        console.error('Error loading categories:', error)
        return { success: false, message: '加载类别失败' }
      }
    },

    // 批量删除类别
    async batchDeleteCategories(ids) {
      try {
        await request.delete('/filters/categories/batch', {
          data: { ids }
        })
        await this.loadCategories()
        return { success: true, message: '批量删除成功' }
      } catch (error) {
        console.error('Error batch deleting categories:', error)
        return { success: false, message: '批量删除失败' }
      }
    },

    // 批量更新类别状态
    async batchUpdateCategoryStatus(ids, is_active) {
      try {
        await request.put('/filters/categories/batch/status', {
          ids,
          is_active
        })
        await this.loadCategories()
        return { success: true, message: `批量${is_active ? '激活' : '停用'}成功` }
      } catch (error) {
        console.error('Error batch updating category status:', error)
        return { success: false, message: `批量${is_active ? '激活' : '停用'}失败` }
      }
    },

    // 查看关键词
    async viewKeywords(category) {
      this.currentCategory = category
      try {
        const params = {}
        if (this.keywordSearchQuery) {
          params.keyword = this.keywordSearchQuery
        }
        const response = await request.get(`/filters/categories/${category.id}/keywords`, { params })
        this.keywords = response.data
        this.keywordDialogVisible = true
        return { success: true }
      } catch (error) {
        console.error('Error loading keywords:', error)
        return { success: false, message: '加载关键词失败' }
      }
    },

    // 打开新增类别对话框
    openAddCategoryDialog() {
      this.categoryForm = {
        id: null,
        name: '',
        description: '',
        is_active: 1
      }
      this.addCategoryDialogVisible = true
    },

    // 打开编辑类别对话框
    openEditCategoryDialog(category) {
      this.categoryForm = {
        id: category.id,
        name: category.name,
        description: category.description,
        is_active: category.is_active
      }
      this.editCategoryDialogVisible = true
    },

    // 创建类别
    async createCategory() {
      try {
        await request.post('/filters/categories', this.categoryForm)
        this.addCategoryDialogVisible = false
        await this.loadCategories()
        return { success: true, message: '类别创建成功' }
      } catch (error) {
        console.error('Error creating category:', error)
        return { success: false, message: '类别创建失败' }
      }
    },

    // 更新类别
    async updateCategory() {
      try {
        await request.put(`/filters/categories/${this.categoryForm.id}`, this.categoryForm)
        this.editCategoryDialogVisible = false
        await this.loadCategories()
        return { success: true, message: '类别更新成功' }
      } catch (error) {
        console.error('Error updating category:', error)
        return { success: false, message: '类别更新失败' }
      }
    },

    // 删除类别
    async deleteCategory(id) {
      try {
        await request.delete(`/filters/categories/${id}`)
        await this.loadCategories()
        return { success: true, message: '类别删除成功' }
      } catch (error) {
        console.error('Error deleting category:', error)
        return { success: false, message: '类别删除失败' }
      }
    },

    // 打开新增关键词对话框
    openAddKeywordDialog() {
      this.keywordForm = {
        id: null,
        keyword: '',
        is_active: 1
      }
      this.addKeywordDialogVisible = true
    },

    // 打开批量添加关键词对话框
    openBatchAddKeywordDialog() {
      this.batchKeywords = ''
      this.batchKeywordDialogVisible = true
    },

    // 创建关键词
    async createKeyword() {
      try {
        await request.post(`/filters/categories/${this.currentCategory.id}/keywords`, this.keywordForm)
        this.addKeywordDialogVisible = false
        await this.viewKeywords(this.currentCategory)
        return { success: true, message: '关键词创建成功' }
      } catch (error) {
        console.error('Error creating keyword:', error)
        return { success: false, message: '关键词创建失败' }
      }
    },

    // 批量创建关键词
    async batchCreateKeywords() {
      try {
        const keywordList = this.batchKeywords
          .split('\n')
          .map(k => k.trim())
          .filter(k => k)
        
        await request.post(`/filters/categories/${this.currentCategory.id}/keywords/batch`, {
          keywords: keywordList
        })
        
        this.batchKeywordDialogVisible = false
        await this.viewKeywords(this.currentCategory)
        return { success: true, message: `成功添加 ${keywordList.length} 个关键词` }
      } catch (error) {
        console.error('Error batch creating keywords:', error)
        return { success: false, message: '批量添加失败' }
      }
    },

    // 删除关键词
    async deleteKeyword(id) {
      try {
        await request.delete(`/filters/keywords/${id}`)
        await this.viewKeywords(this.currentCategory)
        return { success: true, message: '关键词删除成功' }
      } catch (error) {
        console.error('Error deleting keyword:', error)
        return { success: false, message: '关键词删除失败' }
      }
    },

    // 打开导入文档对话框
    openImportDialog() {
      this.importContent = ''
      this.importDialogVisible = true
    },

    // 导入屏蔽词文档
    async importDocument() {
      try {
        if (!this.importContent.trim()) {
          return { success: false, message: '文档内容不能为空' }
        }
        
        const response = await request.post('/filters/import/document', {
          content: this.importContent
        })
        
        this.importDialogVisible = false
        await this.loadCategories()
        return { 
          success: true, 
          message: `文档导入成功：创建了${response.data.categories_created}个类别，${response.data.keywords_created}个关键词` 
        }
      } catch (error) {
        console.error('Error importing document:', error)
        return { success: false, message: '文档导入失败' }
      }
    }
  }
})
