<template>
  <div class="min-h-screen">
    <!-- 顶部导航 -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <router-link to="/" class="text-xl font-bold text-indigo-600">
          EngLearn
        </router-link>
        <span class="text-sm text-gray-500">AI 背单词 Agent</span>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="max-w-4xl mx-auto px-4 py-6">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>
