import { defineStore } from 'pinia'
import request from '@/utils/request'
import { nextTick } from 'vue'
import { exportBookListToExcel } from '@/utils/booklistExport'

export const useInteractiveBookListStore = defineStore('interactiveBookList', {
  state: () => ({
    currentStep: 0,
    loading: false,
    refining: false,
    generating: false,
    
    // 聊天数据
    sessionId: '',
    dialogueMessages: [],
    userInput: '',
    currentState: {},
    
    // 解析后的数据
    parsedData: {
      parsed_requirements: {
        target_audience: '',
        cognitive_level: '',
        categories: [],
        exclude_textbooks: true
      }
    },
    bookListData: {},
    refineForm: {
      refinement_input: ''
    }
  }),

  getters: {
    isDemandComplete: (state) => state.currentState?.completed === true,
    hasMessages: (state) => state.dialogueMessages.length > 0,
    hasBookList: (state) => Object.keys(state.bookListData).length > 0
  },

  actions: {
    // ===== Step 1: Chat =====
    async sendMessage() {
      if (!this.userInput.trim() || this.loading) return { success: false }
      
      const content = this.userInput.trim()
      this.userInput = ''
      
      // 乐观更新 UI
      this.dialogueMessages.push({ role: 'user', content, timestamp: Date.now() })
      this.loading = true
      
      try {
        const res = await request.post('/demand-analysis/dialogue', {
          session_id: this.sessionId || undefined,
          message: content
        })
        
        this.sessionId = res.data.session_id
        this.currentState = res.data.current_state
        
        const lastMsg = res.data.messages[res.data.messages.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          this.dialogueMessages.push(lastMsg)
        }
        
        return { success: true }
      } catch (err) {
        console.error(err)
        this.dialogueMessages.pop() // 回滚
        return { success: false, message: '发送失败' }
      } finally {
        this.loading = false
      }
    },

    resetDialogue() {
      this.sessionId = ''
      this.dialogueMessages = []
      this.currentState = {}
      this.currentStep = 0
    },

    proceedToConfirmation() {
      if (!this.currentState) return { success: false }
      
      const ctx = this.currentState
      const userProfile = ctx.user_profile || {}
      
      this.parsedData.parsed_requirements = {
        target_audience: userProfile.occupation || '通用',
        cognitive_level: userProfile.age_group || '通用',
        exclude_textbooks: true,
        categories: (ctx.book_categories || []).map(c => ({
          category: c.category,
          percentage: c.percentage,
          count: c.count
        })),
        keywords: ctx.user_profile?.reading_preferences || [],
        constraints: ctx.constraints?.other_constraints || []
      }
      
      this.parsedData.request_id = this.sessionId || `temp-${Date.now()}`
      this.currentStep = 1
      
      return { success: true }
    },

    // ===== Step 2: Refine & Generate =====
    refineRequirements() {
      const input = this.refineForm.refinement_input
      if (input) {
        this.parsedData.parsed_requirements.constraints.push(input)
        this.refineForm.refinement_input = ''
        return { success: true, message: '已添加补充说明' }
      }
      return { success: false, message: '请输入补充说明' }
    },

    async confirmAndGenerate() {
      this.generating = true
      try {
        const payload = {
          requirements: this.parsedData.parsed_requirements,
          limit: 20,
          save_to_history: true
        }
        
        const res = await request.post('/book-list/generate', payload)
        this.bookListData = res.data
        this.currentStep = 2
        
        return { success: true, count: res.data.total_count }
      } catch (err) {
        console.error(err)
        return { success: false, message: err.response?.data?.detail || '生成失败' }
      } finally {
        this.generating = false
      }
    },

    // ===== Step 3: Export =====
    exportBookList() {
      try {
        const books = this.bookListData?.books?.length
          ? this.bookListData.books
          : (this.bookListData?.recommendations || [])

        if (!books.length) {
          return { success: false, message: '当前没有可导出的书单' }
        }

        exportBookListToExcel({
          books,
          total_price: this.bookListData?.total_price || 0,
          quality_score: this.bookListData?.quality_score || 0,
          confidence: this.bookListData?.confidence || 0,
          category_distribution: this.bookListData?.category_distribution || {}
        }, {
          booklistName: this.bookListData?.name || this.parsedData?.parsed_requirements?.target_audience || '书单'
        })

        return { success: true, message: '书单已导出为 Excel' }
      } catch (err) {
        console.error('Export interactive booklist failed:', err)
        return { success: false, message: err.message || '导出失败' }
      }
    },

    // Utils
    formatProgress(val) {
      return `${val}%`
    },

    getProgressColor(p) {
      return p > 30 ? '#409eff' : '#e6a23c'
    },

    getScoreColor(s) {
      return s > 0.8 ? '#67c23a' : '#e6a23c'
    },

    goToStep(step) {
      this.currentStep = step
    }
  }
})
