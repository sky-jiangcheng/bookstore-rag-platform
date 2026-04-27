import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/books'
  },
  {
    path: '/books',
    name: 'books',
    component: () => import('../../views/BookManagementView/index.vue'),
    meta: { title: '图书管理' }
  },
  {
    path: '/import',
    name: 'import',
    component: () => import('../../views/DataImport.vue'),
    meta: { title: '数据导入' }
  },
  {
    path: '/duplicates',
    name: 'duplicates',
    component: () => import('../../views/DuplicateCheck.vue'),
    meta: { title: '智能查重' }
  },
  {
    path: '/filters',
    name: 'filters',
    component: () => import('../../views/FilterManagementView/index.vue'),
    meta: { title: '屏蔽配置' }
  },
  {
    path: '/purchase',
    name: 'purchase',
    component: () => import('../../views/PurchaseView/index.vue'),
    meta: { title: '采购管理' }
  },
  {
    path: '/replenishment',
    name: 'replenishment',
    component: () => import('../../views/Replenishment.vue'),
    meta: { title: '补货推荐' }
  }
]

export function createCatalogRouter() {
  return createRouter({
    history: createWebHashHistory(),
    routes
  })
}
