/**
 * 推荐相关工具函数
 */

/**
 * 获取匹配度颜色
 * @param {number} score - 匹配度分数 (0-1)
 * @returns {string} 颜色值
 */
export const getScoreColor = (score) => {
  if (score > 0.8) return '#67c23a'
  if (score > 0.6) return '#409eff'
  if (score > 0.4) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 获取来源类型
 * @param {string} source - 来源标识
 * @returns {string} Element UI标签类型
 */
export const getSourceType = (source) => {
  switch (source) {
    case 'database': return 'primary'
    case 'vector': return 'info'
    case 'popular': return 'warning'
    default: return 'default'
  }
}

/**
 * 获取来源文本
 * @param {string} source - 来源标识
 * @returns {string} 来源中文名
 */
export const getSourceText = (source) => {
  switch (source) {
    case 'database': return '数据库'
    case 'vector': return '向量搜索'
    case 'popular': return '热门推荐'
    default: return '其他'
  }
}

/**
 * 获取难度等级文本
 * @param {string} difficulty - 难度标识
 * @returns {string} 难度中文名
 */
export const getDifficultyText = (difficulty) => {
  const map = {
    'beginner': '入门',
    'intermediate': '进阶',
    'advanced': '高级'
  }
  return map[difficulty] || '不限'
}

/**
 * 获取预算进度颜色
 * @param {number} current - 当前价格
 * @param {number} budget - 预算
 * @returns {string} 颜色值
 */
export const getBudgetProgressColor = (current, budget) => {
  const ratio = current / budget
  if (ratio <= 0.8) return '#67c23a'
  if (ratio <= 1.0) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 格式化价格
 * @param {number} price - 价格
 * @returns {string} 格式化后的价格
 */
export const formatPrice = (price) => {
  return `¥${price.toFixed(2)}`
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} 是否复制成功
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Copy to clipboard failed:', error)
    return false
  }
}

/**
 * 生成随机ID
 * @returns {string} 随机ID
 */
export const generateId = () => {
  return Math.random().toString(36).substring(2, 15)
}
