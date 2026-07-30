<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">阅读文章</h1>
      <router-link to="/" class="text-sm text-indigo-600 hover:underline">
        返回首页
      </router-link>
    </div>

    <!-- 生成文章区域 -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">AI 生成文章</h2>
        <button
          v-if="!article"
          @click="doGenerateArticle"
          :disabled="generatingArticle"
          class="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {{ generatingArticle ? '生成中...' : '生成文章' }}
        </button>
        <button
          v-else
          @click="doGenerateArticle"
          :disabled="generatingArticle"
          class="text-sm text-gray-500 hover:text-indigo-600 disabled:opacity-50"
        >
          {{ generatingArticle ? '重新生成中...' : '重新生成' }}
        </button>
      </div>

      <div v-if="generatingArticle && !article" class="text-center py-8">
        <div class="animate-pulse text-gray-500">
          AI 正在创作文章，请稍候...
        </div>
      </div>

      <div v-else-if="article" class="prose prose-sm max-w-none">
        <div class="whitespace-pre-wrap leading-relaxed text-gray-700" v-html="renderedArticle"></div>
      </div>

      <div v-else class="text-center py-8 text-gray-400">
        点击"生成文章"按钮，AI 将根据今日单词生成一篇英文短文
      </div>

      <div v-if="articleError" class="mt-3 text-sm text-red-500">
        {{ articleError }}
      </div>
    </div>

    <!-- 题目区域 -->
    <div v-if="article" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">阅读理解</h2>
        <button
          v-if="questions.length === 0"
          @click="doGenerateQuestions"
          :disabled="generatingQuestions"
          class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          {{ generatingQuestions ? '生成中...' : '生成题目' }}
        </button>
      </div>

      <div v-if="generatingQuestions" class="text-center py-8">
        <div class="animate-pulse text-gray-500">
          AI 正在出题，请稍候...
        </div>
      </div>

      <div v-else-if="questions.length > 0" class="space-y-6">
        <div
          v-for="(q, idx) in questions"
          :key="idx"
          class="border border-gray-100 rounded-xl p-4"
        >
          <!-- 选择题 -->
          <template v-if="q.type === 'choice'">
            <p class="font-medium text-gray-800 mb-3">
              {{ idx + 1 }}. {{ q.question }}
            </p>
            <div class="space-y-2 mb-3">
              <label
                v-for="(opt, key) in q.options"
                :key="key"
                class="flex items-center gap-2 cursor-pointer p-2 rounded-lg hover:bg-gray-50"
                :class="{ 'bg-green-50 border border-green-200': showAnswers && key === q.answer }"
              >
                <input
                  type="radio"
                  :name="`q${idx}`"
                  :value="key"
                  v-model="userAnswers[idx]"
                  class="text-indigo-600"
                />
                <span class="text-sm text-gray-700">{{ key }}. {{ opt }}</span>
              </label>
            </div>
          </template>

          <!-- 简答题 -->
          <template v-else-if="q.type === 'short_answer'">
            <p class="font-medium text-gray-800 mb-3">
              {{ idx + 1 }}. {{ q.question }}
            </p>
            <textarea
              v-model="userAnswers[idx]"
              class="w-full border border-gray-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
              rows="3"
              placeholder="输入你的答案..."
            ></textarea>
          </template>

          <!-- 原始文本 -->
          <template v-else>
            <p class="text-gray-700 whitespace-pre-wrap">{{ q.question }}</p>
          </template>

          <!-- 答案解析 -->
          <div v-if="showAnswers" class="mt-3 p-3 bg-blue-50 rounded-lg">
            <p class="text-sm font-medium text-blue-800 mb-1">
              答案：{{ q.answer }}
            </p>
            <p class="text-sm text-blue-600" v-if="q.explanation">
              解析：{{ q.explanation }}
            </p>
          </div>
        </div>

        <!-- 显示答案按钮 -->
        <div class="text-center">
          <button
            @click="showAnswers = !showAnswers"
            class="px-6 py-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            {{ showAnswers ? '隐藏答案' : '查看答案解析' }}
          </button>
        </div>
      </div>

      <div v-if="questionsError" class="mt-3 text-sm text-red-500">
        {{ questionsError }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getGeneratedContent, generateArticle, generateQuestions } from '../api'

const props = defineProps({
  recordId: { type: [String, Number], required: true },
})

const article = ref('')
const questions = ref([])
const generatingArticle = ref(false)
const generatingQuestions = ref(false)
const articleError = ref('')
const questionsError = ref('')
const showAnswers = ref(false)
const userAnswers = ref({})

const renderedArticle = computed(() => {
  if (!article.value) return ''
  // 简单的 markdown 加粗渲染
  return article.value.replace(/\*\*(.*?)\*\*/g, '<strong class="text-indigo-700">$1</strong>')
})

onMounted(async () => {
  // 加载已有内容
  try {
    const res = await getGeneratedContent(props.recordId)
    if (res.data.article) {
      article.value = res.data.article
    }
    if (res.data.questions && res.data.questions.length > 0) {
      questions.value = res.data.questions
    }
  } catch (e) {
    console.error('加载内容失败:', e)
  }
})

const doGenerateArticle = async () => {
  generatingArticle.value = true
  articleError.value = ''
  try {
    const res = await generateArticle(props.recordId)
    article.value = res.data.article
  } catch (e) {
    articleError.value = e.response?.data?.detail || '文章生成失败，请检查 LLM 配置'
  } finally {
    generatingArticle.value = false
  }
}

const doGenerateQuestions = async () => {
  generatingQuestions.value = true
  questionsError.value = ''
  try {
    const res = await generateQuestions(props.recordId)
    questions.value = res.data.questions
  } catch (e) {
    questionsError.value = e.response?.data?.detail || '题目生成失败，请检查 LLM 配置'
  } finally {
    generatingQuestions.value = false
  }
}
</script>
