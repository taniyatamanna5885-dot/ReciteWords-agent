<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">学习历史</h1>
      <router-link to="/" class="text-sm text-indigo-600 hover:underline">
        返回首页
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">
      加载中...
    </div>

    <div v-else-if="records.length > 0" class="space-y-3">
      <div
        v-for="record in records"
        :key="record.id"
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-center justify-between"
      >
        <div class="flex items-center gap-4">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium"
            :class="record.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
          >
            {{ record.status === 'completed' ? '✓' : '...' }}
          </div>
          <div>
            <p class="font-medium text-gray-800">{{ record.study_date }}</p>
            <p class="text-sm text-gray-500">{{ record.word_count }} 个单词</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span
            class="text-xs px-2 py-1 rounded-full"
            :class="record.status === 'completed' ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'"
          >
            {{ record.status === 'completed' ? '已完成' : '进行中' }}
          </span>
          <router-link
            v-if="record.status === 'completed'"
            :to="`/article/${record.id}`"
            class="text-sm text-indigo-600 hover:underline"
          >
            查看文章
          </router-link>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12 text-gray-500">
      暂无学习记录
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getHistory } from '../api'

const props = defineProps({
  wordListId: { type: [String, Number], required: true },
})

const loading = ref(true)
const records = ref([])

onMounted(async () => {
  try {
    const res = await getHistory(props.wordListId)
    records.value = res.data
  } catch (e) {
    console.error('获取历史失败:', e)
  } finally {
    loading.value = false
  }
})
</script>
