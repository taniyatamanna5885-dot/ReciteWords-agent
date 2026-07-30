<template>
  <div>
    <!-- 头部信息 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold">今日背诵</h1>
        <p class="text-sm text-gray-500 mt-1" v-if="studyData">
          {{ studyData.word_list.display_name }} · {{ studyData.study_date }}
        </p>
      </div>
      <router-link
        :to="`/history/${wordListId}`"
        class="text-sm text-indigo-600 hover:underline"
      >
        学习历史
      </router-link>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="text-center py-12 text-gray-500">
      正在准备今日单词...
    </div>

    <!-- 已完成状态 -->
    <div v-else-if="completed" class="text-center py-12">
      <div class="text-5xl mb-4">🎉</div>
      <h2 class="text-xl font-semibold mb-2">今日学习已完成！</h2>
      <p class="text-gray-500 mb-6">共学习 {{ words.length }} 个单词</p>
      <button
        @click="goToArticle"
        class="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors"
      >
        生成阅读文章 →
      </button>
    </div>

    <!-- 背单词卡片 -->
    <div v-else-if="words.length > 0">
      <!-- 进度条 -->
      <div class="mb-6">
        <div class="flex justify-between text-sm text-gray-500 mb-1">
          <span>进度</span>
          <span>{{ currentIndex + 1 }} / {{ words.length }}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div
            class="bg-indigo-600 h-2 rounded-full transition-all duration-300"
            :style="{ width: `${((currentIndex + 1) / words.length) * 100}%` }"
          ></div>
        </div>
      </div>

      <!-- 单词卡片 -->
      <div
        class="bg-white rounded-2xl shadow-md border border-gray-100 p-8 mb-6 min-h-[280px] flex flex-col items-center justify-center cursor-pointer select-none"
        @click="flipCard"
      >
        <template v-if="!flipped">
          <h2 class="text-4xl font-bold text-gray-800 mb-3">{{ currentWord.word }}</h2>
          <p class="text-lg text-gray-400">{{ currentWord.phonetic }}</p>
          <p class="text-sm text-gray-400 mt-6">点击卡片查看释义</p>
        </template>
        <template v-else>
          <h2 class="text-3xl font-bold text-gray-800 mb-2">{{ currentWord.word }}</h2>
          <p class="text-sm text-gray-400 mb-4">{{ currentWord.phonetic }}</p>
          <p class="text-xl text-indigo-700 font-medium mb-4">{{ currentWord.meaning }}</p>
          <p class="text-sm text-gray-500 italic text-center" v-if="currentWord.example">
            "{{ currentWord.example }}"
          </p>
        </template>
      </div>

      <!-- 操作按钮 -->
      <div v-if="flipped" class="flex gap-4 justify-center">
        <button
          @click="markAndNext(false)"
          class="px-8 py-3 rounded-lg bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 transition-colors font-medium"
        >
          不认识
        </button>
        <button
          @click="markAndNext(true)"
          class="px-8 py-3 rounded-lg bg-green-50 text-green-600 border border-green-200 hover:bg-green-100 transition-colors font-medium"
        >
          认识
        </button>
      </div>
      <div v-else class="flex justify-center">
        <button
          @click="flipCard"
          class="px-8 py-3 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
        >
          显示释义
        </button>
      </div>
    </div>

    <!-- 无单词 -->
    <div v-else class="text-center py-12 text-gray-500">
      暂无待学单词
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTodayWords, markWord, completeStudy } from '../api'

const props = defineProps({
  wordListId: { type: [String, Number], required: true },
})

const router = useRouter()
const loading = ref(true)
const completed = ref(false)
const studyData = ref(null)
const words = ref([])
const currentIndex = ref(0)
const flipped = ref(false)
const recordId = ref(null)

const currentWord = computed(() => words.value[currentIndex.value] || {})

onMounted(async () => {
  try {
    const res = await getTodayWords(props.wordListId)
    studyData.value = res.data
    words.value = res.data.words
    recordId.value = res.data.record_id
    if (res.data.status === 'completed') {
      completed.value = true
    }
  } catch (e) {
    console.error('获取今日单词失败:', e)
  } finally {
    loading.value = false
  }
})

const flipCard = () => {
  flipped.value = !flipped.value
}

const markAndNext = async (known) => {
  const word = words.value[currentIndex.value]
  try {
    await markWord(word.id, Number(props.wordListId), known)
  } catch (e) {
    console.error('标记失败:', e)
  }

  if (currentIndex.value < words.value.length - 1) {
    currentIndex.value++
    flipped.value = false
  } else {
    // 全部完成
    try {
      await completeStudy(recordId.value)
    } catch (e) {
      console.error('完成学习失败:', e)
    }
    completed.value = true
  }
}

const goToArticle = () => {
  router.push(`/article/${recordId.value}`)
}
</script>
