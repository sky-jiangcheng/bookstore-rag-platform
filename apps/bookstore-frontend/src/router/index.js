import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/import'
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: {
        title: '登录'
      }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/Register.vue'),
      meta: {
        title: '注册'
      }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/Profile.vue'),
      meta: {
        title: '个人中心'
      }
    },
    {
      path: '/import',
      name: 'import',
      component: () => import('../views/DataImport.vue'),
      meta: {
        title: '数据导入'
      }
    },
    {
      path: '/duplicates',
      name: 'duplicates',
      component: () => import('../views/DuplicateCheck.vue'),
      meta: {
        title: '智能查重'
      }
    },
    {
      path: '/replenishment',
      name: 'replenishment',
      component: () => import('../views/Replenishment.vue'),
      meta: {
        title: '补货推荐'
      }
    },
    {
      path: '/recommendation',
      name: 'recommendation',
      component: () => import('../views/Recommendation.vue'),
      meta: {
        title: '新单推荐'
      }
    },
    {
      path: '/logs',
      name: 'logs',
      component: () => import('../views/LogsView.vue'),
      meta: {
        title: '日志管理'
      }
    },
    {
      path: '/purchase',
      name: 'purchase',
      component: () => import('../views/PurchaseView/index.vue'),
      meta: {
        title: '采购管理'
      }
    },
    {
      path: '/books',
      name: 'books',
      component: () => import('../views/BookManagementView/index.vue'),
      meta: {
        title: '图书管理'
      }
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('../views/UserManagementView/index.vue'),
      meta: {
        title: '用户管理'
      }
    },
    {
      path: '/filters',
      name: 'filters',
      component: () => import('../views/FilterManagementView/index.vue'),
      meta: {
        title: '屏蔽配置'
      }
    },
    {
      path: '/intelligent-recommendation',
      redirect: '/booklist-recommendation'
    },
    {
      path: '/interactive-book-list',
      redirect: '/booklist-recommendation'
    },
    {
      path: '/demand-analysis',
      redirect: '/booklist-recommendation'
    },
    {
      path: '/book-list-generation',
      redirect: '/booklist-recommendation'
    },
    {
      path: '/booklist-recommendation',
      name: 'booklist-recommendation',
      component: () => import('../views/BookListRecommendation/index.vue'),
      meta: {
        title: '智能书单生成器'
      }
    },
    {
      path: '/booklist/template/:id',
      name: 'booklist-template',
      component: () => import('../views/BookListShareView/index.vue'),
      meta: {
        title: '分享书单'
      }
    },
    {
      path: '/share/:id',
      name: 'booklist-share',
      component: () => import('../views/BookListShareView/index.vue'),
      meta: {
        title: '分享书单'
      }
    },
    {
      path: '/booklist/shared/:id',
      name: 'booklist-shared',
      component: () => import('../views/BookListShareView/index.vue'),
      meta: {
        title: '分享书单'
      }
    },
    {
      path: '/agent-booklist',
      name: 'agent-booklist',
      component: () => import('../views/AgentBookList/index.vue'),
      meta: {
        title: '书单助手',
        requiresAuth: true
      }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isLoginPage = to.path === '/login' || to.path === '/register'
  const token = localStorage.getItem('access_token')
  
  if (!token && !isLoginPage) {
    next('/login')
  } else if (token && isLoginPage) {
    next('/')
  } else {
    next()
  }
})

router.afterEach((to) => {
  const title = to.meta?.title || to.name || '书店智能管理系统'
  document.title = `${title} - 书店智能管理系统`
})

export default router
