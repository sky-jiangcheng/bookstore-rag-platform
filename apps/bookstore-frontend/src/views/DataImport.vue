<template>
  <div class="data-import-container">
    <h2>数据导入</h2>
    <el-card>
      <el-upload
        class="upload-demo"
        drag
        :http-request="handleHttpRequest"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :file-list="fileList"
        multiple
        :limit="3"
        :on-exceed="handleExceed"
        name="files"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持上传 Excel/CSV 文件，单次最多上传 3 个文件
          </div>
        </template>
      </el-upload>
    </el-card>

    <el-card v-if="importStatus" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>导入进度</span>
        </div>
      </template>
      <el-progress :percentage="importStatus.progress" :status="importStatus.status" />
      <div class="import-status-info" style="margin-top: 10px;">
        <p>状态：{{ importStatus.message }}</p>
        <p v-if="importStatus.successCount">成功：{{ importStatus.successCount }} 条</p>
        <p v-if="importStatus.failureCount">失败：{{ importStatus.failureCount }} 条</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>

import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const fileList = ref([])
const importStatus = ref(null)
const handleUploadSuccess = (response) => {
  importStatus.value = {
    progress: 100,
    status: 'success',
    message: '导入成功',
    successCount: response.successCount,
    failureCount: response.failureCount
  }
  fileList.value = []
}

const handleUploadError = (error) => {
  importStatus.value = {
    progress: 0,
    status: 'exception',
    message: '导入失败'
  }
}

const handleHttpRequest = async (options) => {
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    
    const response = await request.post('/import/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000,
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          options.onProgress({ percent })
        }
      }
    })
    
    options.onSuccess(response.data)
  } catch (error) {
    options.onError(error)
  }
}

const handleExceed = (files, fileList) => {
  ElMessage.warning(`当前限制选择 3 个文件，本次选择了 ${files.length} 个文件，共 ${files.length + fileList.length} 个文件`)
}
</script>

<style scoped>
.data-import-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.import-status-info {
  margin-top: 10px;
  font-size: 14px;
}
</style>