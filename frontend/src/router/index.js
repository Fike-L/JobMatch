import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    component: () => import('../views/Login.vue'),
    meta: {
      title: '登录与注册',
      description: '进入招聘平台，选择求职者、HR 或管理员身份。'
    }
  },
  {
    path: '/',
    component: () => import('../views/Dashboard.vue'),
    meta: {
      roles: ['admin'],
      title: '平台总览',
      description: '查看平台运行情况、角色分布和实时系统日志。'
    }
  },
  {
    path: '/resume',
    component: () => import('../views/ResumePortal.vue'),
    meta: {
      roles: ['seeker'],
      title: '求职工作台',
      description: '统一管理简历、岗位机会和求职动作。'
    }
  },
  {
    path: '/center',
    component: () => import('../views/SeekerCenter.vue'),
    meta: {
      roles: ['seeker'],
      title: '求职者中心',
      description: '查看投递进度、面试安排、收藏和互动反馈。'
    }
  },
  {
    path: '/hr',
    component: () => import('../views/HRConsole.vue'),
    meta: {
      roles: ['hr'],
      title: '招聘控制台',
      description: '集中处理职位发布、人才筛选和候选人沟通。'
    }
  },
  {
    path: '/admin',
    component: () => import('../views/SystemLab.vue'),
    meta: {
      roles: ['admin'],
      title: '后台运营与实验室',
      description: '维护词库、算法参数和平台运营工具。'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const user = JSON.parse(localStorage.getItem('user'))

  if (to.path === '/login') return next()
  if (!user) return next('/login')

  if (to.meta.roles && !to.meta.roles.includes(user.role)) {
    if (user.role === 'seeker') return next('/resume')
    if (user.role === 'hr') return next('/hr')
    if (user.role === 'admin') return next('/')
    return next('/login')
  }

  next()
})

export default router
