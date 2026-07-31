import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // LLM 生成可能较慢
})

// 词表 API
export const getWordLists = () => api.get('/wordlists')
export const getWords = (name, page = 1, size = 20) =>
  api.get(`/wordlists/${name}/words`, { params: { page, size } })
export const uploadWordList = (file, name = '') => {
  const formData = new FormData()
  formData.append('file', file)
  const params = name ? { name } : {}
  return api.post('/wordlists/upload', formData, {
    params,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const deleteWordList = (name) => api.delete(`/wordlists/${name}`)

// 学习 API
export const getTodayWords = (wordListId, count = 0) =>
  api.get('/study/today', { params: { word_list_id: wordListId, count } })
export const markWord = (wordId, wordListId, known) =>
  api.post('/study/mark', { word_id: wordId, word_list_id: wordListId, known })
export const completeStudy = (recordId) =>
  api.post('/study/complete', { record_id: recordId })
export const getHistory = (wordListId) =>
  api.get('/study/history', { params: { word_list_id: wordListId } })

// 生成 API
export const generateArticle = (studyRecordId) =>
  api.post('/generate/article', { study_record_id: studyRecordId })
export const generateQuestions = (studyRecordId) =>
  api.post('/generate/questions', { study_record_id: studyRecordId })
export const getGeneratedContent = (studyRecordId) =>
  api.get(`/generate/content/${studyRecordId}`)

export default api
