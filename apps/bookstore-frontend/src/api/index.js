/**
 * API层封装 - 推荐相关接口
 */
import request from '@/utils/request'

/**
 * 智能推荐API
 */
export const recommendationApi = {
  /**
   * 获取智能推荐
   * @param {Object} params - 推荐参数
   * @param {string} params.user_input - 用户输入
   * @param {number} params.limit - 推荐数量
   */
  getSmartRecommendation: (params) => {
    return request.post('/smart/recommendation', params)
  },

  /**
   * 解析需求
   * @param {Object} data - 解析参数
   * @param {string} data.user_input - 用户输入
   * @param {boolean} data.use_history - 是否使用历史
   */
  parseRequirements: (data) => {
    return request.post('/book-list/parse', data)
  },

  /**
   * 生成书单
   * @param {Object} data - 生成参数
   * @param {string} data.request_id - 请求ID
   * @param {number} data.limit - 数量限制
   * @param {boolean} data.save_to_history - 是否保存历史
   */
  generateBookList: (data) => {
    return request.post('/book-list/generate', data)
  },

  /**
   * 获取书单模板列表
   */
  getTemplates: () => {
    return request.get('/booklist/templates')
  },

  /**
   * 获取书单模板详情
   * @param {number|string} id - 模板ID
   */
  getTemplate: (id) => {
    return request.get(`/booklist/templates/${id}`)
  },

  /**
   * 提交反馈
   * @param {Object} data - 反馈数据
   */
  submitFeedback: (data) => {
    return request.post('/booklist/feedback', data)
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
