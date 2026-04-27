<template>
  <el-dialog v-model="store.shareDialogVisible" title="分享书单" width="600px">
    <el-tabs v-model="store.shareTab">
      <el-tab-pane label="链接分享" name="link">
        <el-form>
          <el-form-item label="分享链接">
            <el-input v-model="store.shareLink" readonly>
              <template #append>
                <el-button @click="handleCopy">复制</el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="导出书单" name="export">
        <el-space wrap>
          <el-button type="primary" @click="handleExportPDF">
            <el-icon><Document /></el-icon>
            导出为PDF
          </el-button>
          <el-button type="success" @click="handleExportExcel">
            <el-icon><Tickets /></el-icon>
            导出为Excel
          </el-button>
          <el-button @click="handleExportImage">
            <el-icon><Picture /></el-icon>
            导出为图片
          </el-button>
        </el-space>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { Document, Tickets, Picture } from '@element-plus/icons-vue'
import { useRecommendationStore } from '@/stores/recommendation'
import { copyToClipboard } from '@/utils/recommendation'
import { exportBookListToExcel } from '@/utils/booklistExport'
import { ElMessage } from 'element-plus'

const store = useRecommendationStore()

const handleCopy = async () => {
  const success = await copyToClipboard(store.shareLink)
  if (success) {
    ElMessage.success('链接已复制到剪贴板')
  } else {
    ElMessage.error('复制失败，请手动复制')
  }
}

const handleExportPDF = () => {
  ElMessage.info('PDF导出功能开发中...')
}

const handleExportExcel = () => {
  try {
    exportBookListToExcel({
      books: store.selectedBooks
    }, {
      booklistName: store.advancedForm.name || '书单'
    })
    ElMessage.success('Excel 导出成功')
  } catch (error) {
    console.error('Export excel failed:', error)
    ElMessage.error(error.message || 'Excel 导出失败')
  }
}

const handleExportImage = () => {
  ElMessage.info('图片导出功能开发中...')
}
</script>
