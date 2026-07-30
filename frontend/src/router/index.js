import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'WordList',
    component: () => import('../views/WordListView.vue'),
  },
  {
    path: '/study/:wordListId',
    name: 'Study',
    component: () => import('../views/StudyView.vue'),
    props: true,
  },
  {
    path: '/article/:recordId',
    name: 'Article',
    component: () => import('../views/ArticleView.vue'),
    props: true,
  },
  {
    path: '/history/:wordListId',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
