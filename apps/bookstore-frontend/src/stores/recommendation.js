import { defineStore } from 'pinia'
import { recommendationApi } from '@/api'
import { exportBookListToExcel } from '@/utils/booklistExport'

/**
 * 智能推荐Store
 * 管理推荐相关的状态和逻辑
 */
export const useRecommendationStore = defineStore('recommendation', {
  state: () => ({
    // 快速推荐模式
    simpleForm: {
      user_input: '',
      limit: 20
    },
    simpleRecommendations: [],
    parsedRequirements: null,
    recommendationReason: '',
    simpleLoading: false,

    // 书单生成器模式
    currentStep: 0,
    advancedForm: {
      name: '',
      description: '',
      book_count: 10,
      budget: 500,
      difficulty: '',
      goals: []
    },
    templates: [],
    selectedTemplate: null,
    analyzing: false,
    analysisResult: {
      keywords: [],
      categories: [],
      reasoning: '',
      books: []
    },
    selectedBooks: [],
    feedback: {
      overall_score: 5,
      accuracy_score: 5,
      price_score: 5,
      diversity_score: 5,
      suggestions: ''
    },

    // 分享
    shareDialogVisible: false,
    shareTab: 'link',
    shareLink: ''
  }),

  getters: {
    // 快速推荐相关
    hasSimpleInput: (state) => state.simpleForm.user_input.trim().length > 0,
    hasSimpleResults: (state) => state.simpleRecommendations.length > 0,

    // 书单生成器相关
    selectedTotalPrice: (state) => {
      return state.selectedBooks.reduce((sum, book) => sum + book.price, 0)
    },

    averageScore: (state) => {
      if (state.selectedBooks.length === 0) return 0
      return state.selectedBooks.reduce((sum, book) => sum + book.score, 0) / state.selectedBooks.length
    },

    allSelected: (state) => {
      return state.selectedBooks.length === state.analysisResult.books.length
    },

    canProceed: (state) => {
      return state.selectedBooks.length > 0 && state.selectedBooks.length <= state.advancedForm.book_count
    },

    budgetProgressColor: (state) => {
      const ratio = state.selectedBooks.reduce((sum, book) => sum + book.price, 0) / state.advancedForm.budget
      if (ratio <= 0.8) return '#67c23a'
      if (ratio <= 1.0) return '#e6a23c'
      return '#f56c6c'
    },

    isOverBudget: (state) => {
      const total = state.selectedBooks.reduce((sum, book) => sum + book.price, 0)
      return total > state.advancedForm.budget
    }
  },

  actions: {
    // ========== 快速推荐模式 ==========
    
    /**
     * 获取智能推荐
     */
    async getSmartRecommendation() {
      if (!this.simpleForm.user_input.trim()) {
        return { success: false, message: '请输入您的阅读需求' }
      }

      this.simpleLoading = true
      try {
        const response = await recommendationApi.getSmartRecommendation({
          user_input: this.simpleForm.user_input,
          limit: this.simpleForm.limit
        })
        
        this.simpleRecommendations = response.data.recommendations || []
        this.parsedRequirements = response.data.parsed_requirements || null
        this.recommendationReason = response.data.recommendation_reason || ''
        
        return { 
          success: true, 
          count: this.simpleRecommendations.length,
          hasResults: this.simpleRecommendations.length > 0
        }
      } catch (error) {
        console.error('Get smart recommendation failed:', error)
        return { success: false, message: '获取推荐失败，请稍后重试' }
      } finally {
        this.simpleLoading = false
      }
    },

    /**
     * 重置快速推荐表单
     */
    resetSimpleForm() {
      this.simpleForm.user_input = ''
      this.simpleForm.limit = 20
      this.simpleRecommendations = []
      this.parsedRequirements = null
      this.recommendationReason = ''
    },

    // ========== 书单生成器模式 ==========

    /**
     * 加载书单模板
     */
    async loadTemplates() {
      try {
        const response = await recommendationApi.getTemplates()
        this.templates = response.data || []
        return { success: true, count: this.templates.length }
      } catch (error) {
        console.error('Failed to load templates:', error)
        this.templates = []
        return { success: false, message: '加载模板失败' }
      }
    },

    /**
     * 选择模板
     */
    selectTemplate(template) {
      this.selectedTemplate = template
      this.advancedForm.name = template.name
      this.advancedForm.description = template.description
      this.advancedForm.book_count = template.book_count
      this.advancedForm.budget = template.budget
      this.advancedForm.difficulty = template.difficulty || ''
      this.advancedForm.goals = template.goals || []
    },

    /**
     * 清空模板
     */
    clearTemplate() {
      this.selectedTemplate = null
      this.advancedForm.name = ''
      this.advancedForm.description = ''
    },

    /**
     * 分析需求
     */
    async analyzeRequirements() {
      if (!this.advancedForm.name.trim()) {
        return { success: false, message: '请输入书单名称' }
      }

      this.analyzing = true
      try {
        // 步骤1：解析需求
        const parseResponse = await recommendationApi.parseRequirements({
          user_input: this.advancedForm.description || this.advancedForm.name,
          use_history: true
        })

        if (!parseResponse.data || !parseResponse.data.request_id) {
          throw new Error('需求解析失败，无法获取有效的request_id')
        }

        // 步骤2：生成书单
        const generateResponse = await recommendationApi.generateBookList({
          request_id: parseResponse.data.request_id,
          limit: this.advancedForm.book_count,
          save_to_history: false
        })

        // 处理返回结果
        this.analysisResult = {
          keywords: parseResponse.data.parsed_requirements.keywords || [],
          categories: parseResponse.data.parsed_requirements.categories || [],
          reasoning: `基于您的需求"${this.advancedForm.name}"，系统已智能分析并推荐${generateResponse.data.total_count}本书籍。`,
          books: generateResponse.data.recommendations.map(r => ({
            book_id: r.book_id,
            barcode: r.barcode,
            title: r.title,
            author: r.author,
            publisher: r.publisher,
            price: r.price,
            stock: r.stock,
            score: r.match_score,
            source: r.source || 'vector',
            category: r.category
          }))
        }

        // 自动选中推荐的书籍
        if (this.analysisResult.books && this.analysisResult.books.length > 0) {
          const recommended = this.analysisResult.books.slice(0, this.advancedForm.book_count)
          this.selectedBooks = recommended.map(book => ({
            ...book,
            remark: ''
          }))
        }

        this.currentStep = 1
        return { success: true, count: this.analysisResult.books.length }
      } catch (error) {
        console.error('Analyze requirements failed:', error)
        return { success: false, message: '需求分析失败，请稍后重试' }
      } finally {
        this.analyzing = false
      }
    },

    /**
     * 重置高级表单
     */
    resetAdvancedForm() {
      this.advancedForm.name = ''
      this.advancedForm.description = ''
      this.advancedForm.book_count = 10
      this.advancedForm.budget = 500
      this.advancedForm.difficulty = ''
      this.advancedForm.goals = []
      this.selectedTemplate = null
      this.currentStep = 0
    },

    /**
     * 处理选择变化
     */
    handleSelectionChange(selection) {
      this.selectedBooks = selection.map(book => ({
        ...book,
        remark: book.remark || ''
      }))
    },

    /**
     * 全选书籍
     */
    selectAllBooks() {
      const booksToSelect = this.analysisResult.books.slice(0, this.advancedForm.book_count)
      this.selectedBooks = booksToSelect.map(book => ({
        ...book,
        remark: book.remark || ''
      }))
    },

    /**
     * 清空选择
     */
    clearSelection() {
      this.selectedBooks = []
    },

    /**
     * 生成书单
     */
    generateBookList() {
      this.currentStep = 2
    },

    /**
     * 创建新书单
     */
    createNewBookList() {
      this.resetAdvancedForm()
      this.selectedBooks = []
      this.analysisResult = {
        keywords: [],
        categories: [],
        reasoning: '',
        books: []
      }
      this.feedback = {
        overall_score: 5,
        accuracy_score: 5,
        price_score: 5,
        diversity_score: 5,
        suggestions: ''
      }
    },

    /**
     * 提交反馈
     */
    async submitFeedback() {
      try {
        await recommendationApi.submitFeedback({
          booklist_name: this.advancedForm.name,
          overall_score: this.feedback.overall_score,
          accuracy_score: this.feedback.accuracy_score,
          price_score: this.feedback.price_score,
          diversity_score: this.feedback.diversity_score,
          suggestions: this.feedback.suggestions,
          selected_books: this.selectedBooks.map(b => b.book_id),
          book_count: this.selectedBooks.length,
          total_price: this.selectedBooks.reduce((sum, book) => sum + book.price, 0),
          average_score: Math.round(this.averageScore * 100)
        })
        return { success: true }
      } catch (error) {
        console.error('Submit feedback failed:', error)
        return { 
          success: false, 
          message: error.response?.data?.detail || '反馈提交失败，请稍后重试'
        }
      }
    },

    /**
     * 导出当前书单为 Excel
     */
    exportBookList() {
      try {
        const books = this.selectedBooks.length > 0
          ? this.selectedBooks
          : this.analysisResult.books

        if (!books || books.length === 0) {
          return { success: false, message: '当前没有可导出的书单' }
        }

        exportBookListToExcel({
          books,
          total_price: this.selectedTotalPrice,
          quality_score: this.averageScore,
          confidence: 0,
          category_distribution: {}
        }, {
          booklistName: this.advancedForm.name || '书单'
        })

        return { success: true, message: '书单已导出为 Excel' }
      } catch (error) {
        console.error('Export booklist failed:', error)
        return { success: false, message: error.message || '导出失败' }
      }
    },

    // ========== 分享相关 ==========

    /**
     * 生成分享链接
     */
    generateShareLink() {
      this.shareLink = `${window.location.origin}/share/${this.generateShareId()}`
      this.shareDialogVisible = true
    },

    /**
     * 生成分享ID
     */
    generateShareId() {
      return Math.random().toString(36).substring(2, 15)
    },

    /**
     * 关闭分享对话框
     */
    closeShareDialog() {
      this.shareDialogVisible = false
    }
  }
})
