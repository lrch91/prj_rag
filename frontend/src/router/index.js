import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/', name: 'Chat', component: () => import('../views/Chat.vue'), meta: { auth: true } },
  { path: '/kbs', name: 'KBs', component: () => import('../views/KBList.vue'), meta: { auth: true } },
  { path: '/kbs/:kbId/docs', name: 'Documents', component: () => import('../views/Documents.vue'), meta: { auth: true } },
  { path: '/users', name: 'Users', component: () => import('../views/Users.vue'), meta: { auth: true, admin: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.auth && !token) return next('/login')
  next()
})

export default router
