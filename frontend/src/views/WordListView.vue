<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">选择词表</h1>

    <div v-if="loading" class="text-center py-12 text-gray-500">
      加载中...
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="wl in wordLists"
        :key="wl.id"
        class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
      >
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-lg font-semibold text-gray-800">{{ wl.display_name }}</h2>
          <span v-if="wl.target" class="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full">
            {{ wl.target }}
          </span>
        </div>
        <p class="text-sm text-gray-500 mb-4">{{ wl.description }}</p>
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-400">{{ wl.word_count }} 词</span>
          <button
            @click="openWordList(wl)"
            class="text-sm text-indigo-600 font-medium hover:text-indigo-800"
          >
            去背诵 →
          </button>
        </div>
      </div>
    </div>

    <div v-if="!loading && wordLists.length === 0" class="text-center py-12 text-gray-500">
      暂无可用词表
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getWordLists } from '../api'

const router = useRouter()
const wordLists = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getWordLists()
    wordLists.value = res.data
  } catch (e) {
    console.error('获取词表失败:', e)
  } finally {
    loading.value = false
  }
})

const openWordList = (wl) => {
  router.push(`/study/${wl.id}`)
}
</script>
