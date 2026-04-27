<template>
  <div class="filter-management-container">
    <el-card class="filter-card">
      <template #header>
        <div class="card-header">
          <span>屏蔽类别管理</span>
          <div class="category-header-actions">
            <el-input
              v-model="categorySearchQuery"
              placeholder="搜索类别名称"
              style="width: 200px; margin-right: 10px"
              clearable
              @keyup.enter="loadCategories"
            >
              <template #prefix>
                <el-icon class="el-input__icon"><Search /></el-icon>
              </template>
              <template #append>
                <el-button @click="loadCategories"><el-icon><Search /></el-icon></el-button>
              </template>
            </el-input>
            <el-button type="success" @click="openImportDialog">
              <el-icon><Upload /></el-icon>
              导入文档
            </el-button>
            <el-button type="primary" @click="openAddCategoryDialog">
              <el-icon><Plus /></el-icon>
              新增类别
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="categories" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="类别名称" />
        <el-table-column prop="description" label="类别描述" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button 
              size="small" 
              @click="viewKeywords(scope.row)"
              :disabled="!scope.row.is_active"
            >
              管理关键词
            </el-button>
            <el-button 
              size="small" 
              type="primary" 
              @click="openEditCategoryDialog(scope.row)"
            >
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteCategory(scope.row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 关键词管理对话框 -->
    <el-dialog
      v-model="keywordDialogVisible"
      title="关键词管理"
      width="80%"
    >
      <div class="keyword-management">
        <div class="keyword-header">
          <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
            <span>{{ currentCategory?.name }} - 关键词列表</span>
            <div style="display: flex; align-items: center;">
              <el-input
                v-model="keywordSearchQuery"
                placeholder="搜索关键词"
                style="width: 200px; margin-right: 10px"
                clearable
                @keyup.enter="viewKeywords(currentCategory)"
              >
                <template #prefix>
                  <el-icon class="el-input__icon"><Search /></el-icon>
                </template>
                <template #append>
                  <el-button @click="viewKeywords(currentCategory)"><el-icon><Search /></el-icon></el-button>
                </template>
              </el-input>
              <el-button type="primary" @click="openAddKeywordDialog">
                新增关键词
              </el-button>
              <el-button type="success" @click="openBatchAddKeywordDialog">
                批量添加
              </el-button>
            </div>
          </div>
        </div>
        
        <el-table :data="keywords" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="keyword" label="关键词" />
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                {{ scope.row.is_active ? '激活' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <el-button 
                size="small" 
                type="danger" 
                @click="deleteKeyword(scope.row.id)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
    
    <!-- 新增类别对话框 -->
    <el-dialog
      v-model="addCategoryDialogVisible"
      title="新增屏蔽类别"
      width="500px"
    >
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="类别名称">
          <el-input v-model="categoryForm.name" placeholder="请输入类别名称" />
        </el-form-item>
        <el-form-item label="类别描述">
          <el-input 
            v-model="categoryForm.description" 
            placeholder="请输入类别描述" 
            type="textarea" 
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="categoryForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addCategoryDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createCategory">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 编辑类别对话框 -->
    <el-dialog
      v-model="editCategoryDialogVisible"
      title="编辑屏蔽类别"
      width="500px"
    >
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="类别名称">
          <el-input v-model="categoryForm.name" placeholder="请输入类别名称" />
        </el-form-item>
        <el-form-item label="类别描述">
          <el-input 
            v-model="categoryForm.description" 
            placeholder="请输入类别描述" 
            type="textarea" 
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="categoryForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editCategoryDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateCategory">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 新增关键词对话框 -->
    <el-dialog
      v-model="addKeywordDialogVisible"
      title="新增关键词"
      width="400px"
    >
      <el-form :model="keywordForm" label-width="80px">
        <el-form-item label="关键词">
          <el-input v-model="keywordForm.keyword" placeholder="请输入关键词" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="keywordForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addKeywordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createKeyword">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 批量添加关键词对话框 -->
    <el-dialog
      v-model="batchKeywordDialogVisible"
      title="批量添加关键词"
      width="500px"
    >
      <el-form label-width="80px">
        <el-form-item label="关键词列表">
          <el-input 
            v-model="batchKeywords"
            type="textarea"
            :rows="6"
            placeholder="请输入关键词，每行一个"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchKeywordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="batchCreateKeywords">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 导入屏蔽词文档对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="导入屏蔽词文档"
      width="600px"
    >
      <el-form label-width="80px">
        <el-form-item label="文档内容">
          <el-input 
            v-model="importContent"
            type="textarea"
            :rows="10"
            placeholder="请粘贴屏蔽词文档内容"
          />
        </el-form-item>
        <el-form-item>
          <el-alert
            title="文档格式说明"
            type="info"
            :closable="false"
            show-icon
          >
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
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="importDocument">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Upload, Search } from '@element-plus/icons-vue'
import request from '../utils/request'

const categories = ref([])
const keywords = ref([])
const currentCategory = ref(null)
const keywordDialogVisible = ref(false)
const addCategoryDialogVisible = ref(false)
const editCategoryDialogVisible = ref(false)
const addKeywordDialogVisible = ref(false)
const batchKeywordDialogVisible = ref(false)
const importDialogVisible = ref(false)
const categorySearchQuery = ref('')
const keywordSearchQuery = ref('')

const categoryForm = reactive({
  id: null,
  name: '',
  description: '',
  is_active: 1
})

const keywordForm = reactive({
  id: null,
  keyword: '',
  is_active: 1
})

const batchKeywords = ref('')
const importContent = ref('')

// 加载类别列表
const loadCategories = async () => {
  try {
    const params = {}
    if (categorySearchQuery.value) {
      params.name = categorySearchQuery.value
    }
    const response = await request.get('/filters/categories', { params })
    categories.value = response.data
  } catch (error) {
    ElMessage.error('加载类别失败')
    console.error('Error loading categories:', error)
  }
}

// 查看关键词
const viewKeywords = async (category) => {
  currentCategory.value = category
  try {
    const params = {}
    if (keywordSearchQuery.value) {
      params.keyword = keywordSearchQuery.value
    }
    const response = await request.get(`/filters/categories/${category.id}/keywords`, { params })
    keywords.value = response.data
    keywordDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载关键词失败')
    console.error('Error loading keywords:', error)
  }
}

// 打开新增类别对话框
const openAddCategoryDialog = () => {
  Object.assign(categoryForm, {
    id: null,
    name: '',
    description: '',
    is_active: 1
  })
  addCategoryDialogVisible.value = true
}

// 打开编辑类别对话框
const openEditCategoryDialog = (category) => {
  Object.assign(categoryForm, {
    id: category.id,
    name: category.name,
    description: category.description,
    is_active: category.is_active
  })
  editCategoryDialogVisible.value = true
}

// 创建类别
const createCategory = async () => {
  try {
    await request.post('/filters/categories', categoryForm)
    ElMessage.success('类别创建成功')
    addCategoryDialogVisible.value = false
    loadCategories()
  } catch (error) {
    ElMessage.error('类别创建失败')
    console.error('Error creating category:', error)
  }
}

// 更新类别
const updateCategory = async () => {
  try {
    await request.put(`/filters/categories/${categoryForm.id}`, categoryForm)
    ElMessage.success('类别更新成功')
    editCategoryDialogVisible.value = false
    loadCategories()
  } catch (error) {
    ElMessage.error('类别更新失败')
    console.error('Error updating category:', error)
  }
}

// 删除类别
const deleteCategory = async (id) => {
  try {
    await request.delete(`/filters/categories/${id}`)
    ElMessage.success('类别删除成功')
    loadCategories()
  } catch (error) {
    ElMessage.error('类别删除失败')
    console.error('Error deleting category:', error)
  }
}

// 打开新增关键词对话框
const openAddKeywordDialog = () => {
  Object.assign(keywordForm, {
    id: null,
    keyword: '',
    is_active: 1
  })
  addKeywordDialogVisible.value = true
}

// 打开批量添加关键词对话框
const openBatchAddKeywordDialog = () => {
  batchKeywords.value = ''
  batchKeywordDialogVisible.value = true
}

// 创建关键词
const createKeyword = async () => {
  try {
    await request.post(`/filters/categories/${currentCategory.value.id}/keywords`, keywordForm)
    ElMessage.success('关键词创建成功')
    addKeywordDialogVisible.value = false
    viewKeywords(currentCategory.value)
  } catch (error) {
    ElMessage.error('关键词创建失败')
    console.error('Error creating keyword:', error)
  }
}

// 批量创建关键词
const batchCreateKeywords = async () => {
  try {
    const keywordList = batchKeywords.value
      .split('\n')
      .map(k => k.trim())
      .filter(k => k)
    
    await request.post(`/filters/categories/${currentCategory.value.id}/keywords/batch`, {
      keywords: keywordList
    })
    
    ElMessage.success(`成功添加 ${keywordList.length} 个关键词`)
    batchKeywordDialogVisible.value = false
    viewKeywords(currentCategory.value)
  } catch (error) {
    ElMessage.error('批量添加失败')
    console.error('Error batch creating keywords:', error)
  }
}

// 删除关键词
const deleteKeyword = async (id) => {
  try {
    await request.delete(`/filters/keywords/${id}`)
    ElMessage.success('关键词删除成功')
    viewKeywords(currentCategory.value)
  } catch (error) {
    ElMessage.error('关键词删除失败')
    console.error('Error deleting keyword:', error)
  }
}

// 打开导入文档对话框
const openImportDialog = () => {
  importContent.value = ''
  importDialogVisible.value = true
}

// 导入屏蔽词文档
const importDocument = async () => {
  try {
    if (!importContent.value.trim()) {
      ElMessage.error('文档内容不能为空')
      return
    }
    
    const response = await request.post('/filters/import/document', {
      content: importContent.value
    })
    
    ElMessage.success(`文档导入成功：创建了${response.data.categories_created}个类别，${response.data.keywords_created}个关键词`)
    importDialogVisible.value = false
    loadCategories()
  } catch (error) {
    ElMessage.error('文档导入失败')
    console.error('Error importing document:', error)
  }
}

// 初始加载
onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.filter-management-container {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-header-actions {
  display: flex;
  align-items: center;
}

.category-header-actions > * {
  margin-left: 10px;
}

.category-header-actions > *:first-child {
  margin-left: 0;
}

.keyword-management {
  padding: 10px;
}

.keyword-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eaeaea;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.el-table {
  margin-top: 20px;
}
</style>
