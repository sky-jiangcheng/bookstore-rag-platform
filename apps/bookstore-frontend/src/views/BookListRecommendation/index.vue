<template>
  <div class="booklist-recommendation-container">
    <h2>智能书单生成器</h2>
    
    <!-- 步骤指示器 -->
    <el-steps :active="store.currentStep" finish-status="success" align-center style="margin-bottom: 30px;">
      <el-step title="需求分析" description="输入您的书单需求" />
      <el-step title="结果确认" description="查看和调整推荐结果" />
      <el-step title="书单生成" description="生成最终书单" />
    </el-steps>

    <!-- 步骤1：需求分析 -->
    <step-one v-show="store.currentStep === 0" class="step-card" />

    <!-- 步骤2：结果确认 -->
    <step-two v-show="store.currentStep === 1" class="step-card" />

    <!-- 步骤3：书单生成 -->
    <step-three v-show="store.currentStep === 2" class="step-card" />

    <!-- 分享对话框 -->
    <share-dialog />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRecommendationStore } from '@/stores/recommendation'

// 书单生成器组件
import StepOne from './components/StepOne.vue'
import StepTwo from './components/StepTwo.vue'
import StepThree from './components/StepThree.vue'
import ShareDialog from './components/ShareDialog.vue'

const store = useRecommendationStore()

// 初始化
onMounted(() => {
  store.loadTemplates()
})
</script>

<style scoped>
.booklist-recommendation-container {
  padding: 20px;
}

.step-card {
  min-height: 600px;
}

@media (max-width: 768px) {
  .booklist-recommendation-container {
    padding: 10px;
  }
  
  .step-card {
    min-height: auto;
  }
}
</style>
