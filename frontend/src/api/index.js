import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    // 全局错误提示
    const msg = err.response?.data?.detail || err.message || '请求失败'
    window.dispatchEvent(new CustomEvent('app-error', { detail: msg }))
    return Promise.reject(err)
  }
)

export default {
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),

  // KB
  listKBs: () => api.get('/kbs'),
  createKB: (params) => api.post('/kbs', null, { params }),
  deleteKB: (id) => api.delete(`/kbs/${id}`),
  grantKB: (kbId, targetUserId, permission) => api.post(`/kbs/${kbId}/permissions?target_user_id=${targetUserId}&permission=${permission}`),
  listKBPerms: (kbId) => api.get(`/kbs/${kbId}/permissions`),
  revokeKB: (kbId, targetUserId) => api.delete(`/kbs/${kbId}/permissions/${targetUserId}`),

  // Documents
  listDocs: (kbId, params) => api.get(`/kbs/${kbId}/documents`, { params }),
  uploadDoc: (kbId, formData) => api.post(`/kbs/${kbId}/documents/upload`, formData),
  deleteDoc: (kbId, docId) => api.delete(`/kbs/${kbId}/documents/${docId}`),
  updateDoc: (kbId, docId, formData) => api.post(`/kbs/${kbId}/documents/${docId}/update`, formData),
  docStatus: (kbId, docId) => api.get(`/kbs/${kbId}/documents/${docId}/status`),

  // Models
  listModels: () => api.get('/models'),

  // QA
  ask: (data) => api.post('/qa/ask', data),
  askStream: (data) => api.post('/qa/ask/stream', data, { responseType: 'stream' }),

  // Conversations
  listConvs: () => api.get('/conversations'),
  getConv: (id) => api.get(`/conversations/${id}`),
  delConv: (id) => api.delete(`/conversations/${id}`),

  // Categories & Tags
  listCategories: (kbId) => api.get(`/kbs/${kbId}/categories`),
  listTags: (kbId) => api.get(`/kbs/${kbId}/tags`),
  createCategory: (kbId, params) => api.post(`/kbs/${kbId}/categories`, null, { params }),
  createTag: (kbId, params) => api.post(`/kbs/${kbId}/tags`, null, { params }),

  // Users (Admin)
  listUsers: () => api.get('/users'),
  createUser: (params) => api.post('/users', null, { params }),
  updateUser: (id, params) => api.put(`/users/${id}`, null, { params }),
  deactivateUser: (id) => api.delete(`/users/${id}`),
}
