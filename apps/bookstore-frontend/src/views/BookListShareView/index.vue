<template>
  <div class="booklist-share-container">
    <el-card class="share-card">
      <template #header>
        <div class="card-header">
          <h2>{{ isTemplateShare ? '书单模板分享' : '分享书单' }}</h2>
          <el-tag type="info">ID: {{ shareId }}</el-tag>
        </div>
      </template>

      <el-skeleton v-if="loading" :rows="6" animated />

      <template v-else>
        <el-alert
          :title="isTemplateShare ? '模板分享入口' : '书单分享入口'"
          type="info"
          :closable="false"
          show-icon
          class="share-alert"
        />

        <div v-if="templateDetail" class="share-content">
          <h3>{{ templateDetail.name }}</h3>
          <p>{{ templateDetail.description }}</p>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="书籍数量">
              {{ templateDetail.book_count }} 本
            </el-descriptions-item>
            <el-descriptions-item label="预算">
              ¥{{ templateDetail.budget }}
            </el-descriptions-item>
            <el-descriptions-item label="难度">
              {{ templateDetail.difficulty || '不限' }}
            </el-descriptions-item>
            <el-descriptions-item label="标签">
              <el-tag
                v-for="tag in templateDetail.tags || []"
                :key="tag"
                size="small"
                style="margin-right: 6px;"
              >
                {{ tag }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div v-else class="share-content">
          <p>
            当前链接是共享入口，已与后端路径对齐。你可以返回智能书单生成器继续生成，或者直接关闭页面。
          </p>
        </div>

        <el-space wrap>
          <el-button type="primary" @click="goToBookList">
            打开智能书单生成器
          </el-button>
          <el-button @click="goHome">
            返回首页
          </el-button>
        </el-space>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { recommendationApi } from '@/api'

const route = useRoute()
const router = useRouter()

const shareId = computed(() => route.params.id || 'unknown')
const isTemplateShare = computed(() => route.path.startsWith('/booklist/template/'))
const loading = ref(false)
const templateDetail = ref(null)

const loadShareData = async () => {
  templateDetail.value = null

  if (!isTemplateShare.value) {
    return
  }

  loading.value = true
  try {
    const response = await recommendationApi.getTemplate(shareId.value)
    templateDetail.value = response.data || null
  } catch (error) {
    console.error('Load template failed:', error)
  } finally {
    loading.value = false
  }
}

const goToBookList = () => {
  router.push('/booklist-recommendation')
}

const goHome = () => {
  router.push('/')
}

onMounted(loadShareData)
watch(() => route.fullPath, loadShareData)
</script>

<style scoped>
.booklist-share-container {
  padding: 20px;
}

.share-card {
  max-width: 960px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.share-alert {
  margin-bottom: 20px;
}

.share-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  line-height: 1.7;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .booklist-share-container {
    padding: 10px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
