<template>
  <el-dialog v-model="store.importDialogVisible" title="导入屏蔽词文档" width="600px">
    <el-form label-width="80px">
      <el-form-item label="文档内容">
        <el-input 
          v-model="store.importContent"
          type="textarea"
          :rows="10"
          placeholder="请粘贴屏蔽词文档内容"
        />
      </el-form-item>
      <el-form-item>
        <el-alert title="文档格式说明" type="info" :closable="false" show-icon>
          <ul>
            <li>一行只有2-3个字的是关键词（类别）</li>
            <li>关键词下面的词是该关键词对应的屏蔽词</li>
            <li>不同类别之间用空行分隔</li>
          </ul>
        </el-alert>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="store.importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImport">确定</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { useFilterStore } from '@/stores/filter'
import { ElMessage } from 'element-plus'

const store = useFilterStore()

const handleImport = async () => {
  const result = await store.importDocument()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}
</script>
