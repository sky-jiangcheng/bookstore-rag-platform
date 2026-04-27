import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../../views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../../views/Register.vue'),
    meta: { title: '注册' }
  }
]

export function createAuthRouter() {
  return createRouter({
    history: createWebHashHistory(),
    routes
  })
}
