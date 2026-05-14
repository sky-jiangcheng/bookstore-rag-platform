import axios from 'axios'
import { getApiBaseUrl } from '@/utils/apiBase'

const base = getApiBaseUrl()
const client = axios.create({ baseURL: base, timeout: 30000 })

export function setAuthToken(token) {
  if (token) client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  else delete client.defaults.headers.common['Authorization']
}

export async function parseRequirements(payload) {
  const resp = await client.post('/agent/parse', payload)
  return resp.data
}

export async function generateBookList(payload) {
  const resp = await client.post('/agent/generate', payload)
  return resp.data
}

export async function getTemplates() {
  const resp = await client.get('/booklist/templates')
  return resp.data
}

export async function getTemplate(id) {
  const resp = await client.get(`/booklist/templates/${encodeURIComponent(id)}`)
  return resp.data
}

export async function submitFeedback(data) {
  const resp = await client.post('/booklist/feedback', data)
  return resp.data
}

export async function exportBookList(data) {
  const resp = await client.post('/book-list/export-excel', data, {
    responseType: 'blob'  // 重要：接收二进制文件
  })
  return resp.data
}

export default {
  setAuthToken,
  parseRequirements,
  generateBookList,
  getTemplates,
  getTemplate,
  submitFeedback,
  exportBookList,
}
