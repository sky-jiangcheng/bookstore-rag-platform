import axios, { AxiosInstance } from 'axios'

const getBaseUrl = () => {
  // Vite env variable used by frontend
  // Ensure VITE_API_BASE_URL is like: https://your-agentic-host.example.com/api/v1
  // Fallback to relative /api/v1 for dev proxy
  // @ts-ignore
  return (import.meta.env?.VITE_API_BASE_URL as string) || '/api/v1'
}

let api: AxiosInstance = axios.create({ baseURL: getBaseUrl(), timeout: 30000 })

export function configureApi(options: { baseUrl?: string; token?: string } = {}) {
  if (options.baseUrl) {
    api = axios.create({ baseURL: options.baseUrl, timeout: 30000 })
  }
  if (options.token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${options.token}`
  }
}

export function setAuthToken(token: string | null) {
  if (token) api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  else delete api.defaults.headers.common['Authorization']
}

// Types (minimal, expand as needed)
export interface Book {
  book_id?: string
  barcode?: string
  title?: string
  author?: string
  publisher?: string
  price?: number
  stock?: number
  match_score?: number
  category?: string
  source?: string
  remark?: string
}

export interface ParsedRequirements {
  target_audience?: Record<string, any>
  cognitive_level?: string
  categories?: Array<Record<string, any>>
  keywords?: string[]
  constraints?: Record<string, any>
}

export interface ParseRequirementsResponse {
  request_id: string
  parsed_requirements: ParsedRequirements
  confidence_score?: number
  needs_confirmation?: boolean
  message?: string
}

export interface GenerateBookListResponse {
  request_id?: string
  session_id?: number | null
  book_list_id?: number | null
  requirements?: ParsedRequirements
  recommendations?: Book[]
  total_count?: number
  category_distribution?: Record<string, number>
  generation_time_ms?: number
  success?: boolean
  message?: string
}

// Client methods
export async function parseRequirements(user_input: string, use_history = false): Promise<ParseRequirementsResponse> {
  const payload = { user_input, use_history }
  const resp = await api.post('/book-list/parse', payload)
  return resp.data
}

export async function generateBookList(params: {
  request_id?: string
  requirements?: ParsedRequirements
  limit?: number
  save_to_history?: boolean
}): Promise<GenerateBookListResponse> {
  const resp = await api.post('/book-list/generate', params)
  return resp.data
}

export async function getBookListSession(request_id: string): Promise<any> {
  const resp = await api.get(`/book-list/${encodeURIComponent(request_id)}`)
  return resp.data
}

export async function health(): Promise<{ status: string }> {
  const resp = await api.get('/health')
  return resp.data
}

// Helper: create an instance-bound client (for tests)
export function createClientInstance(baseUrl?: string, token?: string) {
  const inst = axios.create({ baseURL: baseUrl || getBaseUrl(), timeout: 30000 })
  if (token) inst.defaults.headers.common['Authorization'] = `Bearer ${token}`
  return {
    parseRequirements: async (user_input: string, use_history = false) => (await inst.post('/book-list/parse', { user_input, use_history })).data,
    generateBookList: async (params: any) => (await inst.post('/book-list/generate', params)).data,
    getBookListSession: async (request_id: string) => (await inst.get(`/book-list/${encodeURIComponent(request_id)}`)).data,
    health: async () => (await inst.get('/health')).data,
  }
}

export default {
  configureApi,
  setAuthToken,
  parseRequirements,
  generateBookList,
  getBookListSession,
  health,
  createClientInstance,
}
