import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/booklist-recommendation'
  },
  {
    path: '/booklist-recommendation',
    name: 'booklist-recommendation',
    component: () => import('../../views/BookListRecommendation/index.vue'),
    meta: { title: '智能书单生成' }
  },
  {
    path: '/agent-booklist',
    name: 'agent-booklist',
    component: () => import('../../views/AgentBookList/index.vue'),
    meta: { title: 'Agent 书单工作台' }
  },
  {
    path: '/demand-analysis',
    name: 'demand-analysis',
    component: () => import('../../views/Recommendation.vue'),
    meta: { title: '需求分析' }
  }
]

export function createRagRouter() {
  return createRouter({
    history: createWebHashHistory(),
    routes
  })
}
