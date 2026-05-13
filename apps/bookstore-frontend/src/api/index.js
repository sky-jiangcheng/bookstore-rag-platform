/**
 * API层封装 - 推荐相关接口
 */
import request from '@/utils/request'

/**
 * 智能推荐API
 */
import * as booklistClient from './booklistClient'

export const recommendationApi = {
  /**
   * 获取智能推荐 - 保留原有快速推荐接口
   */
  getSmartRecommendation: (params) => {
    return request.post('/smart/recommendation', params)
  },

  /**
   * 解析需求 -> 通过 gateway 转发到 agentic-rag
   */
  parseRequirements: (data) => {
    return booklistClient.parseRequirements(data)
  },

  /**
   * 生成书单 -> 通过 gateway 转发到 agentic-rag
   */
  generateBookList: (data) => {
    return booklistClient.generateBookList(data)
  },

  /**
   * 获取书单模板列表
   */
  getTemplates: () => {
    return booklistClient.getTemplates()
  },

  /**
   * 获取书单模板详情
   */
  getTemplate: (id) => {
    return booklistClient.getTemplate(id)
  },

  /**
   * 提交反馈
   */
  submitFeedback: (data) => {
    return booklistClient.submitFeedback(data)
  }
}

/**
 * 采购相关API
 */
export const purchaseApi = {
  /**
   * 添加到采购列表
   * @param {Array} items - 采购项列表
   */
  addToPurchase: (items) => {
    return request.post('/purchase/batch', items)
  }
}

/**
 * 书籍相关API
 */
export const bookApi = {
  /**
   * 获取书籍列表
   * @param {Object} params - 查询参数
   */
  getList: (params) => {
    return request.get('/books', { params })
  },

  /**
   * 获取书籍详情
   * @param {number} id - 书籍ID
   */
  getDetail: (id) => {
    return request.get(`/books/${id}`)
  },

  /**
   * 更新书籍
   * @param {number} id - 书籍ID
   * @param {Object} data - 书籍数据
   */
  update: (id, data) => {
    return request.put(`/books/${id}`, data)
  },

  /**
   * 更新库存
   * @param {number} id - 书籍ID
   * @param {Object} data - 库存数据
   */
  updateStock: (id, data) => {
    return request.put(`/books/${id}/stock`, data)
  }
}

export default {
  recommendation: recommendationApi,
  purchase: purchaseApi,
  book: bookApi
}
