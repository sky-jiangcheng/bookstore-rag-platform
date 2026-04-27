<template>
  <div class="agent-booklist-container">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <h2>书单助手</h2>
          <div class="header-actions">
            <el-tag :type="connectionStatus.type" effect="dark" size="small">
              {{ connectionStatus.text }}
            </el-tag>
            <el-button v-if="messages.length > 0" link @click="clearChat">
              <el-icon><Refresh /></el-icon> 清空对话
            </el-button>
          </div>
        </div>
      </template>

      <!-- 功能介绍 -->
      <div class="feature-intro" v-if="messages.length === 0">
        <div class="intro-content">
          <el-icon :size="64" color="#409EFF"><ChatDotRound /></el-icon>
          <div class="intro-text">
            <h3>智能对话式书单助手</h3>
            <p class="intro-description">通过自然语言对话，AI 将为您分析需求并生成个性化书单。支持多种场景，如学科学习、兴趣爱好、年龄阶段等。</p>
          </div>
        </div>
      </div>

      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success" style="margin: 20px 0;">
        <el-step title="需求分析" :description="stepDescriptions[0]" />
        <el-step title="智能检索" :description="stepDescriptions[1]" />
        <el-step title="生成书单" :description="stepDescriptions[2]" />
      </el-steps>

      <!-- 消息列表 -->
      <div ref="messageContainer" class="message-container">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <h4>请告诉我您的阅读需求，例如：</h4>
          <div class="example-chips">
            <el-tag 
              v-for="example in examples" 
              :key="example"
              class="example-chip"
              type="primary"
              effect="light"
              @click="useExample(example)"
            >
              {{ example }}
            </el-tag>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'" class="message user-message">
            <div class="message-content">
              <el-avatar :size="36" :icon="UserFilled" class="user-avatar" />
              <div class="message-bubble">
                {{ message.content }}
              </div>
            </div>
          </div>

          <!-- AI 消息 -->
          <div v-else class="message ai-message">
            <div class="message-content">
              <el-avatar :size="36" :icon="ChatDotRound" class="ai-avatar" />
              <div class="message-bubble">
                <!-- 普通文本消息 -->
                <div v-if="message.type === 'text'" class="text-message">
                  {{ message.content }}
                </div>

                <!-- 思考过程 -->
                <div v-else-if="message.type === 'thought'" class="thought-message">
                  <el-icon class="thinking-icon"><Loading /></el-icon>
                  <span>{{ message.content }}</span>
                </div>

                <!-- 步骤完成 -->
                <div v-else-if="message.type === 'step_complete'" class="step-complete-message">
                  <el-icon class="success-icon" color="#67C23A"><CircleCheck /></el-icon>
                  <span>{{ message.content }}</span>
                  <el-tag v-if="message.data" size="small" type="success" style="margin-left: 10px;">
                    {{ getStepSummary(message) }}
                  </el-tag>
                </div>

                <!-- 澄清问题 -->
                <div v-else-if="message.type === 'clarification_needed'" class="clarification-message">
                  <el-icon class="info-icon" color="#E6A23C"><InfoFilled /></el-icon>
                  <div>
                    <p>{{ message.content }}</p>
                    <ul v-if="message.questions" class="question-list">
                      <li v-for="(q, i) in message.questions" :key="i">{{ q }}</li>
                    </ul>
                  </div>
                </div>

                <!-- 错误消息 -->
                <div v-else-if="message.type === 'error'" class="error-message">
                  <el-icon class="error-icon" color="#F56C6C"><CircleClose /></el-icon>
                  <span>{{ message.content }}</span>
                </div>

                <!-- 最终结果 - 书单 -->
                <div v-else-if="message.type === 'complete'" class="complete-message">
                  <el-card class="result-card">
                    <template #header>
                      <div class="result-header">
                        <h3>书单生成完成！</h3>
                        <el-tag type="success" size="small">
                          {{ message.booklist?.books?.length || 0 }} 本书
                        </el-tag>
                      </div>
                    </template>
                    <div class="result-summary">
                      <p>为您推荐了 {{ message.booklist?.books?.length || 0 }} 本书，总价 ¥{{ message.booklist?.total_price?.toFixed(2) || '0.00' }}</p>
                    </div>
                    <BookListResult :data="message.booklist" />
                  </el-card>
                </div>

                <!-- 默认消息 -->
                <div v-else class="text-message">
                  {{ message.content }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 正在输入指示器 -->
        <div v-if="isTyping" class="typing-indicator">
          <div class="message ai-message">
            <div class="message-content">
              <el-avatar :size="36" :icon="ChatDotRound" class="ai-avatar" />
              <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="描述您的阅读需求，例如：我想为大学生准备一份编程入门书单..."
          :disabled="isProcessing"
          @keyup.enter.ctrl="sendMessage"
          class="input-textarea"
        >
          <template #append>
            <el-button 
              type="primary" 
              :loading="isProcessing"
              :disabled="!inputMessage.trim()"
              @click="sendMessage"
              size="large"
            >
              <el-icon><Message /></el-icon>
              发送
            </el-button>
          </template>
        </el-input>
        <div class="input-hint">
          <span>按 Ctrl + Enter 快速发送</span>
        </div>
      </div>
    </el-card>

    <!-- 推理过程面板 -->
    <ReasoningPanel 
      v-if="reasoningSteps.length > 0" 
      :steps="reasoningSteps"
      class="reasoning-panel"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  ChatDotRound, 
  UserFilled, 
  Loading, 
  CircleCheck, 
  CircleClose,
  InfoFilled,
  Promotion,
  Message,
  Refresh
} from '@element-plus/icons-vue'
import BookListResult from './components/BookListResult.vue'
import ReasoningPanel from './components/ReasoningPanel.vue'
import { useAgentStore } from '@/stores/agent'

const store = useAgentStore()
const messages = ref([])
const inputMessage = ref('')
const isProcessing = ref(false)
const isTyping = ref(false)
const currentStep = ref(0)
const reasoningSteps = ref([])
const messageContainer = ref(null)

const examples = [
  '我想为大学生准备一份编程入门书单',
  '请推荐一些Python数据分析的书籍',
  '需要给10岁孩子选科普读物',
  '预算500元，想买算法和数据结构的书'
]

const stepDescriptions = computed(() => {
  return [
    currentStep.value > 0 ? '已完成' : '分析您的需求',
    currentStep.value > 1 ? '已完成' : '搜索相关书籍',
    currentStep.value > 2 ? '已完成' : '精选推荐'
  ]
})

const connectionStatus = computed(() => {
  if (store.isConnected) {
    return { type: 'success', text: '已连接' }
  }
  return { type: 'danger', text: '未连接' }
})

// 使用示例
const useExample = (example) => {
  inputMessage.value = example
}

// 发送消息
const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || isProcessing.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    type: 'text',
    content: message
  })

  inputMessage.value = ''
  isProcessing.value = true
  isTyping.value = true

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  try {
    // 调用 Agent API
    await store.sendMessage(message, (msg) => {
      handleAgentMessage(msg)
    })
  } catch (error) {
    ElMessage.error('发送消息失败: ' + error.message)
    messages.value.push({
      role: 'assistant',
      type: 'error',
      content: '抱歉，处理您的请求时发生错误。请稍后重试。'
    })
  } finally {
    isProcessing.value = false
    isTyping.value = false
    await nextTick()
    scrollToBottom()
  }
}

// 处理 Agent 消息
const handleAgentMessage = (msg) => {
  switch (msg.type) {
    case 'start':
      currentStep.value = 0
      reasoningSteps.value = []
      break
      
    case 'step_start':
      currentStep.value = msg.step
      messages.value.push({
        role: 'assistant',
        type: 'thought',
        content: msg.content
      })
      reasoningSteps.value.push({
        step: msg.step,
        name: msg.step_name,
        status: 'running',
        content: msg.content
      })
      break
      
    case 'step_complete':
      messages.value.push({
        role: 'assistant',
        type: 'step_complete',
        content: msg.content,
        data: msg.data
      })
      // 更新推理步骤
      const step = reasoningSteps.value.find(s => s.step === msg.step)
      if (step) {
        step.status = 'completed'
        step.result = msg.data
      }
      break
      
    case 'thought':
      // 思考过程，不显示在消息列表中
      break
      
    case 'result':
      // 中间结果
      break
      
    case 'clarification_needed':
      messages.value.push({
        role: 'assistant',
        type: 'clarification_needed',
        content: msg.content,
        questions: msg.questions
      })
      break
      
    case 'complete':
      messages.value.push({
        role: 'assistant',
        type: 'complete',
        content: msg.content,
        booklist: msg.booklist,
        requirement: msg.requirement
      })
      currentStep.value = 3
      break
      
    case 'error':
      messages.value.push({
        role: 'assistant',
        type: 'error',
        content: msg.content
      })
      break
  }
  
  nextTick(() => scrollToBottom())
}

// 获取步骤摘要
const getStepSummary = (message) => {
  if (!message.data) return ''
  const data = message.data
  if (data.candidate_count !== undefined) {
    return `找到 ${data.candidate_count} 本书`
  }
  if (data.confidence !== undefined) {
    return `置信度 ${Math.round(data.confidence * 100)}%`
  }
  return ''
}

// 滚动到底部
const scrollToBottom = () => {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

// 清空对话
const clearChat = () => {
  messages.value = []
  currentStep.value = 0
  reasoningSteps.value = []
  store.clearSession()
}

// 连接 WebSocket
onMounted(() => {
  store.connect()
})

// 断开连接
onUnmounted(() => {
  store.disconnect()
})
</script>

<style scoped>
.agent-booklist-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
}

.main-card {
  flex: 1;
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 功能介绍 */
.feature-intro {
  padding: 30px 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecf5ff 100%);
  border-radius: 8px;
  margin: 20px;
}

.intro-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.intro-text h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.intro-description {
  margin: 0;
  color: #606266;
  line-height: 1.5;
}

/* 消息容器 */
.message-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  max-height: 550px;
}

.welcome-message {
  text-align: center;
  padding: 30px 20px;
  color: #606266;
}

.welcome-message h4 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 500;
}

.example-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.example-chip {
  cursor: pointer;
  transition: all 0.3s;
  padding: 8px 16px;
  border-radius: 20px;
}

.example-chip:hover {
  background-color: #ecf5ff;
  color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

/* 消息样式 */
.message-wrapper {
  margin-bottom: 20px;
}

.message {
  display: flex;
  margin-bottom: 12px;
}

.message-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 85%;
}

.user-message {
  justify-content: flex-end;
}

.user-message .message-content {
  flex-direction: row-reverse;
}

.ai-message {
  justify-content: flex-start;
}

.message-bubble {
  padding: 16px 20px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  max-width: 100%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.user-message .message-bubble {
  background-color: #409EFF;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message .message-bubble {
  background-color: #ffffff;
  color: #303133;
  border-bottom-left-radius: 4px;
  border: 1px solid #e4e7ed;
}

.user-avatar {
  background-color: #409EFF;
  font-size: 18px;
}

.ai-avatar {
  background-color: #67C23A;
  font-size: 18px;
}

/* 消息类型样式 */
.thought-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
}

.thinking-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-complete-message {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.success-icon {
  font-size: 20px;
}

.clarification-message {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background-color: #fdf6ec;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #fde2c0;
}

.question-list {
  margin: 10px 0 0 0;
  padding-left: 20px;
  color: #606266;
}

.question-list li {
  margin-bottom: 6px;
  line-height: 1.4;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #f56c6c;
}

/* 结果卡片 */
.result-card {
  margin-top: 10px;
  border-radius: 12px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.result-summary {
  margin: 15px 0;
  padding: 12px;
  background-color: #f0f9ff;
  border-radius: 8px;
  color: #606266;
}

/* 输入区域 */
.input-area {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background-color: #f9f9f9;
}

.input-textarea {
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.input-textarea:focus {
  border-color: #409EFF;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.input-hint {
  display: flex;
  justify-content: flex-start;
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

/* 正在输入指示器 */
.typing-indicator {
  margin-top: 12px;
}

.typing-dots {
  display: flex;
  gap: 6px;
  padding: 16px 20px;
  background-color: #ffffff;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.typing-dots span {
  width: 10px;
  height: 10px;
  background-color: #909399;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite both;
}

.typing-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* 推理面板 */
.reasoning-panel {
  width: 380px;
  flex-shrink: 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 992px) {
  .agent-booklist-container {
    flex-direction: column;
  }
  
  .reasoning-panel {
    width: 100%;
    margin-top: 20px;
  }
  
  .intro-content {
    flex-direction: column;
    text-align: center;
    gap: 15px;
  }
  
  .message-content {
    max-width: 95%;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 768px) {
  .agent-booklist-container {
    padding: 10px;
  }
  
  .main-card {
    margin: 0;
  }
  
  .feature-intro {
    margin: 10px;
    padding: 20px 15px;
  }
  
  .message-container {
    padding: 15px;
  }
  
  .input-area {
    padding: 15px;
  }
}
</style>
