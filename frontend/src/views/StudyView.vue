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
      正在准备...
    </div>

    <!-- 选择学习数量 -->
    <div v-else-if="!started">
      <!-- 词表为空：显示上传界面 -->
      <div v-if="!hasWords" class="text-center py-12">
        <div class="text-4xl mb-4">📚</div>
        <h2 class="text-xl font-semibold mb-2">{{ studyData?.word_list?.display_name || '此词表' }} 还没有单词</h2>
        <p class="text-gray-500 mb-6">上传 JSON 文件添加词汇，格式如下：</p>
        <pre v-if="showExample" class="bg-gray-50 rounded p-3 text-xs text-gray-600 mb-4 text-left max-w-lg mx-auto overflow-x-auto">[
  {"word": "abandon", "phonetic": "/əˈbændən/", "meaning": "v. 放弃", "example": "He abandoned his plan."},
  {"word": "abstract", "phonetic": "/ˈæbstrækt/", "meaning": "adj. 抽象的", "example": "abstract art"}
]</pre>
        <p v-else class="mb-4">
          <a href="#" class="text-indigo-600 hover:underline text-sm" @click.prevent="showExample = true">查看 JSON 格式示例</a>
        </p>
        <div class="flex flex-col items-center gap-3">
          <input
            ref="fileInput"
            type="file"
            accept=".json"
            @change="handleUpload"
            class="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
          <span v-if="uploadMsg" :class="uploadOk ? 'text-green-600' : 'text-red-600'" class="text-sm">
            {{ uploadMsg }}
          </span>
        </div>
      </div>

      <!-- 词表有词：显示学习数量选择 -->
      <div v-else class="text-center py-12">
        <h2 class="text-xl font-semibold mb-2">本次学多少个？</h2>
        <p class="text-gray-500 mb-6" v-if="studyData">
          {{ studyData.word_list.display_name }} · 词表共 {{ studyData.total_available }} 词
        </p>
        <div class="flex items-center justify-center gap-3 mb-4">
          <button
            v-for="n in quickOptions"
            :key="n"
            @click="selectedCount = n"
            class="px-4 py-2 rounded-lg border text-sm transition-colors"
            :class="selectedCount === n
              ? 'bg-indigo-600 text-white border-indigo-600'
              : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400'"
          >
            {{ n }}
          </button>
        </div>
        <div class="flex items-center justify-center gap-2 mb-6">
          <span class="text-sm text-gray-500">自定义:</span>
          <input
            v-model.number="selectedCount"
            type="number"
            min="1"
            max="200"
            class="w-20 px-3 py-2 border border-gray-300 rounded-lg text-center focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
          />
          <span class="text-sm text-gray-500">个</span>
        </div>
        <button
          @click="startStudy"
          :disabled="!selectedCount || selectedCount < 1"
          class="bg-indigo-600 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          开始学习
        </button>
      </div>
    </div>

    <!-- 已完成状态 -->
    <div v-else-if="completed" class="text-center py-12">
      <div class="text-5xl mb-4">🎉</div>
      <h2 class="text-xl font-semibold mb-2">本轮学习完成！</h2>
      <p class="text-gray-500 mb-6">共学习 {{ words.length }} 个单词</p>
      <div class="flex gap-4 justify-center">
        <button
          @click="goToArticle"
          class="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          生成阅读文章 →
        </button>
        <button
          @click="continueStudy"
          class="border border-indigo-300 text-indigo-600 px-6 py-3 rounded-lg hover:bg-indigo-50 transition-colors"
        >
          继续学习
        </button>
      </div>
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
import { getTodayWords, markWord, completeStudy, uploadWordList } from '../api'

const props = defineProps({
  wordListId: { type: [String, Number], required: true },
})

const router = useRouter()
const loading = ref(true)
const started = ref(false)
const completed = ref(false)
const studyData = ref(null)
const words = ref([])
const currentIndex = ref(0)
const flipped = ref(false)
const recordId = ref(null)
const selectedCount = ref(10)
const quickOptions = [5, 10, 15, 20, 30, 50]
const showExample = ref(false)
const uploadMsg = ref('')
const uploadOk = ref(false)

const hasWords = computed(() => {
  return studyData.value && studyData.value.total_available > 0
})

const currentWord = computed(() => words.value[currentIndex.value] || {})

onMounted(async () => {
  try {
    // 获取词表信息（不创建学习记录）
    const res = await getTodayWords(props.wordListId, 0)
    studyData.value = res.data
  } catch (e) {
    console.error('获取词表信息失败:', e)
  } finally {
    loading.value = false
  }
})

const startStudy = async () => {
  loading.value = true
  try {
    const res = await getTodayWords(props.wordListId, selectedCount.value)
    studyData.value = res.data
    words.value = res.data.words
    recordId.value = res.data.record_id
    currentIndex.value = 0
    flipped.value = false
    started.value = true
    completed.value = false
  } catch (e) {
    console.error('获取今日单词失败:', e)
  } finally {
    loading.value = false
  }
}

const continueStudy = () => {
  started.value = false
  completed.value = false
  words.value = []
  currentIndex.value = 0
  flipped.value = false
}

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

const refreshWordList = async () => {
  try {
    const res = await getTodayWords(props.wordListId, 0)
    studyData.value = res.data
  } catch (e) {
    console.error('获取词表信息失败:', e)
  }
}

const handleUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  uploadMsg.value = ''
  try {
    // 传入当前词表名称，确保上传到当前词表
    const listName = studyData.value?.word_list?.name || ''
    const res = await uploadWordList(file, listName)
    uploadOk.value = true
    uploadMsg.value = `上传成功！共 ${res.data.word_count} 个单词`
    // 刷新词表信息，会自动切换到学习选择界面
    await refreshWordList()
  } catch (e) {
    uploadOk.value = false
    uploadMsg.value = e.response?.data?.detail || '上传失败，请检查文件格式'
  }
  event.target.value = ''
}

const goToArticle = () => {
  router.push(`/article/${recordId.value}`)
}
</script>
