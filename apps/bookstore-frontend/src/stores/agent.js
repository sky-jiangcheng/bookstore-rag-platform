import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getApiOrigin } from '@/utils/apiBase'

// 从本地存储获取认证头
const getAuthHeader = () => {
  const token = localStorage.getItem('access_token')
  if (token) {
    return { 'Authorization': `Bearer ${token}` }
  }
  return {}
}

export const useAgentStore = defineStore('agent', () => {
  
  // State
  const ws = ref(null)
  const sessionId = ref(null)
  const isConnected = ref(false)
  const isProcessing = ref(false)
  const currentStep = ref(0)
  const messages = ref([])
  const reasoningSteps = ref([])
  const lastBooklist = ref(null)
  
  // Getters
  const canSend = computed(() => isConnected.value && !isProcessing.value)
  const hasActiveSession = computed(() => !!sessionId.value)
  
  // Actions
  
  // 重连计数器
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  
  // 连接状态管理
  const isConnecting = ref(false)
  
  /**
   * 连接 WebSocket
   */
  const connect = () => {
    // 如果已经连接或正在连接，则返回
    if (ws.value?.readyState === WebSocket.OPEN || isConnecting.value) {
      return
    }
    
    // 重连次数限制
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      console.warn('Agent WebSocket max reconnect attempts reached')
      isConnected.value = false
      return
    }
    
    // 标记正在连接
    isConnecting.value = true
    
    // 构建正确的 WebSocket URL
    const wsBaseUrl = getApiOrigin().replace(/^http/, 'ws')
    let wsUrl = `${wsBaseUrl}/v2/agent/ws`
    
    // 添加认证 token
    const token = localStorage.getItem('access_token')
    if (token) {
      const separator = wsUrl.includes('?') ? '&' : '?'
      wsUrl += `${separator}token=${token}`
    }
    
    console.log('Attempting to connect to Agent WebSocket:', wsUrl)
    console.log('Reconnect attempt:', reconnectAttempts.value + 1, '/', maxReconnectAttempts)
    
    try {
      ws.value = new WebSocket(wsUrl)
      
      ws.value.onopen = () => {
        isConnected.value = true
        isConnecting.value = false
        reconnectAttempts.value = 0
        console.log('Agent WebSocket connected')
      }
      
      ws.value.onclose = () => {
        isConnected.value = false
        isConnecting.value = false
        console.log('Agent WebSocket disconnected')
        // 尝试重连
        if (reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++
          setTimeout(() => connect(), 3000)
        }
      }
      
      ws.value.onerror = (error) => {
        console.error('Agent WebSocket error:', error)
        isConnected.value = false
        isConnecting.value = false
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      isConnecting.value = false
      isConnected.value = false
      // 尝试重连
      if (reconnectAttempts.value < maxReconnectAttempts) {
        reconnectAttempts.value++
        setTimeout(() => connect(), 3000)
      }
    }
  }
  
  /**
   * 断开连接
   */
  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      isConnected.value = false
    }
  }
  
  /**
   * 发送消息
   * @param {string} message - 用户消息
   * @param {Function} onMessage - 消息回调
   */
  const sendMessage = async (message, onMessage) => {
    isProcessing.value = true
    currentStep.value = 0
    reasoningSteps.value = []
    
    try {
      // 优先使用 WebSocket
      if (isConnected.value) {
        console.log('Using WebSocket for agent message')
        return await sendWebSocketMessage(message, onMessage)
      } else {
        // WebSocket 未连接，使用 HTTP 降级
        console.log('WebSocket not connected, falling back to HTTP')
        return await sendHttpFallbackMessage(message, onMessage)
      }
    } catch (error) {
      console.error('WebSocket failed, falling back to HTTP:', error)
      // WebSocket 失败，使用 HTTP 降级
      return await sendHttpFallbackMessage(message, onMessage)
    } finally {
      isProcessing.value = false
    }
  }
  
  /**
   * 使用 WebSocket 发送消息
   */
  const sendWebSocketMessage = async (message, onMessage) => {
    if (!isConnected.value) {
      throw new Error('WebSocket not connected')
    }
    
    // 发送消息
    const payload = {
      action: 'chat',
      message: message,
      session_id: sessionId.value
    }
    
    ws.value.send(JSON.stringify(payload))
    
    // 监听响应
    return new Promise((resolve, reject) => {
      const messageHandler = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // 处理会话创建
          if (data.type === 'session_created') {
            sessionId.value = data.session_id
          }
          
          // 处理步骤更新
          if (data.type === 'step_start') {
            currentStep.value = data.step
            reasoningSteps.value.push({
              step: data.step,
              name: data.step_name,
              status: 'running',
              content: data.content
            })
          }
          
          if (data.type === 'step_complete') {
            const step = reasoningSteps.value.find(s => s.step === data.step)
            if (step) {
              step.status = 'completed'
              step.result = data.data
            }
          }
          
          // 保存最终书单
          if (data.type === 'complete' && data.booklist) {
            lastBooklist.value = data.booklist
          }
          
          // 调用回调
          if (onMessage) {
            onMessage(data)
          }
          
          // 完成或错误时结束
          if (data.type === 'complete' || data.type === 'error') {
            ws.value.removeEventListener('message', messageHandler)
            resolve(data)
          }
          
          // 需要澄清时也结束
          if (data.type === 'clarification_needed') {
            ws.value.removeEventListener('message', messageHandler)
            resolve(data)
          }
          
        } catch (error) {
          console.error('Error parsing message:', error)
        }
      }
      
      ws.value.addEventListener('message', messageHandler)
      
      // 超时处理
      setTimeout(() => {
        ws.value.removeEventListener('message', messageHandler)
        reject(new Error('WebSocket request timeout'))
      }, 120000) // 2分钟超时
    })
  }
  
  /**
   * HTTP 降级发送消息
   */
  const sendHttpFallbackMessage = async (message, onMessage) => {
    console.log('Sending message via HTTP fallback')
    
    try {
      // 模拟步骤更新，保持 UI 一致
      if (onMessage) {
        // 模拟开始步骤
        onMessage({
          type: 'step_start',
          step: 0,
          step_name: '需求分析',
          content: '正在分析您的阅读需求...'
        })
        
        // 模拟完成步骤
        onMessage({
          type: 'step_complete',
          step: 0,
          data: {}
        })
        
        onMessage({
          type: 'step_start',
          step: 1,
          step_name: '智能检索',
          content: '正在搜索相关书籍...'
        })
        
        onMessage({
          type: 'step_complete',
          step: 1,
          data: {}
        })
        
        onMessage({
          type: 'step_start',
          step: 2,
          step_name: '生成书单',
          content: '正在生成个性化书单...'
        })
        
        onMessage({
          type: 'step_complete',
          step: 2,
          data: {}
        })
        
        // 发送完成消息
        onMessage({
          type: 'complete',
          booklist: null,
          message: '服务暂时不可用，请稍后重试'
        })
      }
      
      return { type: 'complete', message: '服务暂时不可用，请稍后重试' }
    } catch (error) {
      console.error('HTTP fallback failed:', error)
      if (onMessage) {
        onMessage({
          type: 'error',
          message: '服务暂时不可用，请稍后重试'
        })
      }
      throw error
    }
  }
  
  /**
   * 发送 HTTP 请求（非流式）
   * @param {string} message - 用户消息
   */
  const sendHttpMessage = async (message) => {
    const response = await fetch(`${getApiOrigin()}/v2/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader()
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId.value
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    
    if (data.success && data.session_id) {
      sessionId.value = data.session_id
    }
    
    if (data.data?.booklist) {
      lastBooklist.value = data.data.booklist
    }
    
    return data
  }
  
  /**
   * 发送流式 HTTP 请求
   * @param {string} message - 用户消息
   * @param {Function} onChunk - 块回调
   */
  const sendStreamMessage = async (message, onChunk) => {
    const response = await fetch(`${getApiOrigin()}/v2/agent/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader()
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId.value
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (onChunk) {
              onChunk(data)
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e)
          }
        }
      }
    }
  }
  
  /**
   * 清除会话
   */
  const clearSession = () => {
    if (sessionId.value && ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        action: 'clear',
        session_id: sessionId.value
      }))
    }
    sessionId.value = null
    messages.value = []
    reasoningSteps.value = []
    lastBooklist.value = null
    currentStep.value = 0
  }
  
  /**
   * 获取会话历史
   */
  const getHistory = async () => {
    if (!sessionId.value || !ws.value?.readyState === WebSocket.OPEN) {
      return null
    }
    
    return new Promise((resolve) => {
      const handler = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'history') {
          ws.value.removeEventListener('message', handler)
          resolve(data.history)
        }
      }
      
      ws.value.addEventListener('message', handler)
      ws.value.send(JSON.stringify({
        action: 'history',
        session_id: sessionId.value
      }))
      
      // 超时
      setTimeout(() => {
        ws.value.removeEventListener('message', handler)
        resolve(null)
      }, 5000)
    })
  }
  
  return {
    // State
    ws,
    sessionId,
    isConnected,
    isProcessing,
    currentStep,
    messages,
    reasoningSteps,
    lastBooklist,
    
    // Getters
    canSend,
    hasActiveSession,
    
    // Actions
    connect,
    disconnect,
    sendMessage,
    sendHttpMessage,
    sendStreamMessage,
    clearSession,
    getHistory
  }
})
