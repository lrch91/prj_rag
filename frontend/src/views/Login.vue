<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-brand">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="#2563eb"/>
            <path d="M12 20h24M12 29h18M14 14l-3 6v18a3 3 0 003 3h20a3 3 0 003-3V20l-3-6H14z" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1>KnowledgeBase</h1>
        <p class="subtitle">Enterprise RAG Platform</p>
      </div>
      <form @submit.prevent="login" class="login-form">
        <label class="field">
          <span class="field-label">用户名</span>
          <input v-model="username" placeholder="admin" autocomplete="username" />
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <input v-model="password" type="password" placeholder="admin123" autocomplete="current-password" />
        </label>
        <p v-if="err" class="err">{{ err }}</p>
        <button type="submit" :disabled="loading" class="login-btn">
          <span>{{ loading ? '登录中...' : '登 录' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const username = ref('')
const password = ref('')
const err = ref('')
const loading = ref(false)

async function login() {
  err.value = ''
  if (!username.value || !password.value) { err.value = '请输入用户名和密码'; return }
  loading.value = true
  try {
    const r = await api.login({ username: username.value, password: password.value })
    localStorage.setItem('token', r.data.access_token)
    router.replace('/')
  } catch (e) {
    err.value = e.response?.data?.detail || '登录失败'
  }
  loading.value = false
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 50%, #f0fdf4 100%);
}
.login-card {
  width: 400px; max-width: 90vw;
  background: var(--color-surface); border: 2px solid var(--color-border);
  border-radius: var(--radius-xl); padding: 48px 44px 40px;
  box-shadow: var(--shadow-lg);
  animation: cardIn 0.5s var(--spring);
}
@keyframes cardIn { from { opacity: 0; transform: translateY(20px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
.login-header { text-align: center; margin-bottom: 32px; }
.login-brand { margin-bottom: 14px; }
.login-header h1 { font-family: var(--font-display); font-size: 26px; font-weight: 700; margin-bottom: 4px; }
.subtitle { font-size: 13px; color: var(--color-text-secondary); font-weight: 600; letter-spacing: 0.03em; }
.login-form { display: flex; flex-direction: column; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field-label { font-family: var(--font-display); font-size: 12px; color: var(--color-text-secondary); font-weight: 600; }
.err { color: var(--color-danger); font-size: 13px; font-weight: 600; }
.login-btn { width: 100%; justify-content: center; padding: 14px; font-size: 15px; }
</style>
