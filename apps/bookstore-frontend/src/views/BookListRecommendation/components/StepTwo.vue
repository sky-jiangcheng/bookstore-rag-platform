<template>
  <el-card class="step-card">
    <template #header>
      <div class="card-header">
        <span><el-icon><DocumentChecked /></el-icon> 步骤2：结果确认</span>
        <el-button type="info" size="small" @click="goBack">返回修改</el-button>
      </div>
    </template>

    <div class="analysis-result">
      <h4>需求解析结果</h4>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="书单名称">
          {{ store.advancedForm.name }}
        </el-descriptions-item>
        <el-descriptions-item label="目标数量">
          {{ store.advancedForm.book_count }} 本
        </el-descriptions-item>
        <el-descriptions-item label="预算范围">
          ¥{{ store.advancedForm.budget }}
        </el-descriptions-item>
        <el-descriptions-item label="难度等级">
          {{ getDifficultyText(store.advancedForm.difficulty) }}
        </el-descriptions-item>
        <el-descriptions-item label="关键词" :span="2">
          <el-tag v-for="keyword in store.analysisResult.keywords" :key="keyword" style="margin-right: 5px;">
            {{ keyword }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="分类偏好" :span="2">
          <el-tag v-for="cat in store.analysisResult.categories" :key="cat.category" type="success" style="margin-right: 10px;">
            {{ cat.category }} ({{ cat.percentage }}%, {{ cat.count }}本)
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="阅读目标" :span="2">
          <el-tag v-for="goal in store.advancedForm.goals" :key="goal" type="warning" style="margin-right: 5px;">
            {{ goal }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-alert
        v-if="store.analysisResult.reasoning"
        :title="分析逻辑"
        type="info"
        :closable="false"
        show-icon
        style="margin-top: 15px;"
      >
        {{ store.analysisResult.reasoning }}
      </el-alert>
    </div>

    <el-divider />

    <div class="recommended-books">
      <div class="books-header">
        <h4>推荐书籍 ({{ store.selectedBooks.length }}/{{ store.advancedForm.book_count }})</h4>
        <el-space>
          <span>已选总价: ¥{{ store.selectedTotalPrice.toFixed(2) }}</span>
          <el-button type="success" size="small" @click="handleSelectAll" :disabled="store.allSelected">
            全选
          </el-button>
          <el-button size="small" @click="handleClearSelection">
            清空选择
          </el-button>
        </el-space>
      </div>

      <el-table
        :data="store.analysisResult.books"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="book_id" label="ID" width="80" />
        <el-table-column prop="title" label="书名" min-width="200" />
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="publisher" label="出版社" width="150" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            ¥{{ scope.row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="score" label="匹配度" width="120">
          <template #default="scope">
            <el-progress :percentage="Math.round(scope.row.score * 100)" :color="getScoreColor(scope.row.score)" />
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="100">
          <template #default="scope">
            <el-tag :type="getSourceType(scope.row.source)" size="small">
              {{ getSourceText(scope.row.source) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="store.selectedBooks.length > store.advancedForm.book_count" class="warning-box">
        <el-alert
          title="注意"
          :description="`您选择了 ${store.selectedBooks.length} 本书，超过了目标数量 ${store.advancedForm.book_count} 本，请调整选择`"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>

      <div class="step-buttons">
        <el-button type="primary" @click="handleGenerate" :disabled="!store.canProceed" size="large">
          <el-icon><Select /></el-icon>
          生成书单
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { DocumentChecked, Select } from '@element-plus/icons-vue'
import { useRecommendationStore } from '@/stores/recommendation'
import { getScoreColor, getSourceType, getSourceText, getDifficultyText } from '@/utils/recommendation'

const store = useRecommendationStore()

const goBack = () => {
  store.currentStep = 0
}

const handleSelectionChange = (selection) => {
  store.handleSelectionChange(selection)
}

const handleSelectAll = () => {
  store.selectAllBooks()
}

const handleClearSelection = () => {
  store.clearSelection()
}

const handleGenerate = () => {
  store.generateBookList()
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

.analysis-result {
  margin-bottom: 20px;
}

.analysis-result h4 {
  margin-bottom: 15px;
  color: #409eff;
}

.recommended-books h4 {
  margin-bottom: 15px;
  color: #409eff;
}

.books-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.warning-box {
  margin-top: 15px;
}

.step-buttons {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}
</style>
