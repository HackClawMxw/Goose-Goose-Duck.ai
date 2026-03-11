import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'lobby',
      component: () => import('@/views/Lobby.vue')
    },
    {
      path: '/game/:id',
      name: 'game',
      component: () => import('@/views/Game.vue')
    }
  ]
})

export default router
