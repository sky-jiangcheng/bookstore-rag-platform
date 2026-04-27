<template>
  <el-card class="step-card">
    <template #header>
      <div class="card-header">
        <span><el-icon><Edit /></el-icon> 步骤1：需求分析</span>
        <el-tag type="info">书单模板</el-tag>
      </div>
    </template>

    <div class="template-section">
      <h4>快速选择模板</h4>
      <el-row :gutter="20">
        <el-col :span="8" v-for="template in store.templates" :key="template.id">
          <el-card
            :class="['template-card', { active: store.selectedTemplate?.id === template.id }]"
            @click="handleSelectTemplate(template)"
            shadow="hover"
          >
            <div class="template-content">
              <h5>{{ template.name }}</h5>
              <p>{{ template.description }}</p>
              <div class="template-tags">
                <el-tag v-for="tag in template.tags" :key="tag" size="small">
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-button link type="primary" @click="handleClearTemplate">清空模板</el-button>
    </div>

    <el-divider />

    <el-form :model="store.advancedForm" label-width="100px">
      <el-form-item label="书单名称">
        <el-input v-model="store.advancedForm.name" placeholder="例如：Python入门学习书单" />
      </el-form-item>

      <el-form-item label="需求描述">
        <el-input
          v-model="store.advancedForm.description"
          type="textarea"
          :rows="6"
          placeholder="请详细描述您的书单需求，例如：适合初学者的Python编程书籍，包含基础语法、实战项目、进阶话题等，预算在500元以内..."
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="书籍数量">
            <el-select v-model="store.advancedForm.book_count" style="width: 100%">
              <el-option label="5本" :value="5" />
              <el-option label="10本" :value="10" />
              <el-option label="15本" :value="15" />
              <el-option label="20本" :value="20" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="预算范围">
            <el-input-number
              v-model="store.advancedForm.budget"
              :min="0"
              :max="10000"
              :step="100"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="难度等级">
            <el-select v-model="store.advancedForm.difficulty" style="width: 100%">
              <el-option label="不限" value="" />
              <el-option label="入门" value="beginner" />
              <el-option label="进阶" value="intermediate" />
              <el-option label="高级" value="advanced" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="阅读目标">
        <el-checkbox-group v-model="store.advancedForm.goals">
          <el-checkbox label="学习编程语言" value="学习编程语言" />
          <el-checkbox label="算法与数据结构" value="算法与数据结构" />
          <el-checkbox label="机器学习" value="机器学习" />
          <el-checkbox label="Web开发" value="Web开发" />
          <el-checkbox label="移动开发" value="移动开发" />
          <el-checkbox label="数据分析" value="数据分析" />
          <el-checkbox label="系统架构" value="系统架构" />
          <el-checkbox label="其他" value="其他" />
        </el-checkbox-group>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleAnalyze" :loading="store.analyzing">
          <el-icon><Search /></el-icon>
          分析需求
        </el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { Edit, Search } from '@element-plus/icons-vue'
import { useRecommendationStore } from '@/stores/recommendation'

const store = useRecommendationStore()

const handleSelectTemplate = (template) => {
  store.selectTemplate(template)
}

const handleClearTemplate = () => {
  store.clearTemplate()
}

const handleAnalyze = async () => {
  const result = await store.analyzeRequirements()

  if (!result.success) {
    ElMessage.error(result.message)
  } else {
    ElMessage.success('需求分析完成')
  }
}

const handleReset = () => {
  store.resetAdvancedForm()
}
</script>

<style scoped>
.step-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-section {
  margin-bottom: 20px;
}

.template-section h4 {
  margin-bottom: 15px;
  color: #409eff;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.template-card:hover {
  transform: translateY(-5px);
}

.template-card.active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.template-content h5 {
  margin: 0 0 10px 0;
  color: #333;
}

.template-content p {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
}

.template-tags {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}
</style>
