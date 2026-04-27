<template>
  <el-card class="reasoning-panel">
    <template #header>
      <div class="panel-header">
        <span>推理过程</span>
        <el-tag size="small" :type="overallStatus.type">
          {{ overallStatus.text }}
        </el-tag>
      </div>
    </template>

    <el-timeline>
      <el-timeline-item
        v-for="step in steps"
        :key="step.step"
        :type="getStepStatusType(step.status)"
        :icon="getStepIcon(step.status)"
        :timestamp="step.name"
      >
        <div class="step-content">
          <p class="step-description">{{ step.content }}</p>
          
          <!-- 步骤结果 -->
          <div v-if="step.result" class="step-result">
            <el-descriptions :column="1" size="small">
              <el-descriptions-item 
                v-for="(value, key) in formatResult(step.result)" 
                :key="key"
                :label="key"
              >
                {{ value }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'

const props = defineProps({
  steps: {
    type: Array,
    required: true,
    default: () => []
  }
})

// 整体状态
const overallStatus = computed(() => {
  const lastStep = props.steps[props.steps.length - 1]
  if (!lastStep) {
    return { type: 'info', text: '等待开始' }
  }
  
  if (lastStep.status === 'completed') {
    return { type: 'success', text: '已完成' }
  }
  
  if (lastStep.status === 'running') {
    return { type: 'primary', text: '进行中' }
  }
  
  if (lastStep.status === 'error') {
    return { type: 'danger', text: '出错' }
  }
  
  return { type: 'info', text: '等待中' }
})

// 获取步骤状态类型
const getStepStatusType = (status) => {
  const map = {
    'running': 'primary',
    'completed': 'success',
    'error': 'danger',
    'waiting': 'info'
  }
  return map[status] || 'info'
}

// 获取步骤图标
const getStepIcon = (status) => {
  const map = {
    'running': Loading,
    'completed': CircleCheck,
    'error': CircleClose
  }
  return map[status]
}

// 格式化结果数据
const formatResult = (result) => {
  const formatted = {}
  
  for (const [key, value] of Object.entries(result)) {
    // 跳过复杂对象
    if (typeof value === 'object' && value !== null) {
      continue
    }
    
    // 格式化键名
    const formattedKey = key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
    
    // 格式化值
    let formattedValue = value
    if (typeof value === 'number') {
      if (key.includes('score') || key.includes('confidence')) {
        formattedValue = `${Math.round(value * 100)}%`
      } else if (key.includes('price')) {
        formattedValue = `¥${value.toFixed(2)}`
      }
    }
    
    formatted[formattedKey] = formattedValue
  }
  
  return formatted
}
</script>

<style scoped>
.reasoning-panel {
  height: fit-content;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-content {
  padding: 8px 0;
}

.step-description {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.step-result {
  margin-top: 8px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

:deep(.el-timeline-item__node) {
  background-color: transparent;
}

:deep(.el-timeline-item__icon) {
  font-size: 16px;
}
</style>
