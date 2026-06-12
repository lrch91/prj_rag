<template>
  <aside class="sidebar" :class="{ collapsed: collapsed && !isMobile, open: !collapsed, mobile: isMobile }">
    <div class="sidebar-top">
      <div class="logo-area">
        <div class="logo-mark">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#2563eb"/>
            <path d="M8 13h16M8 20h12M9 9l-2 4v12a2 2 0 002 2h14a2 2 0 002-2V13l-2-4H9z" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-name">KnowledgeBase</span>
          <span class="logo-sub">RAG Platform</span>
        </div>
        <button v-if="isMobile" class="close-btn" @click="emit('close')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <button v-else class="collapse-btn" @click="emit('toggle')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline v-if="collapsed" points="9 18 15 12 9 6"/><polyline v-else points="15 18 9 12 15 6"/></svg>
        </button>
      </div>

      <nav class="nav-links">
        <router-link to="/" class="nav-item" @click="isMobile && emit('close')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <span class="nav-label">智能问答</span>
        </router-link>
        <router-link to="/kbs" v-if="!isViewer" class="nav-item" @click="isMobile && emit('close')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
          <span class="nav-label">知识库</span>
        </router-link>
        <router-link to="/users" v-if="isAdmin" class="nav-item" @click="isMobile && emit('close')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <span class="nav-label">用户管理</span>
        </router-link>
      </nav>
    </div>

    <div class="sidebar-bottom">
      <div class="user-area" @click="menuOpen = !menuOpen">
        <div class="user-avatar">{{ avatarChar }}</div>
        <div class="user-info">
          <span class="user-name">{{ username }}</span>
          <span class="user-role">{{ isAdmin ? '管理员' : '成员' }}</span>
        </div>
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="chevron" :class="{ open: menuOpen }"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
      <div v-if="menuOpen" class="user-dropdown">
        <button class="dropdown-item" @click="logout">退出登录</button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const props = defineProps({
  collapsed: { type: Boolean, default: false },
  isMobile: { type: Boolean, default: false },
})
const emit = defineEmits(['toggle', 'close'])

const router = useRouter()
const username = ref('')
const isAdmin = ref(false)
const isViewer = ref(false)
const menuOpen = ref(false)
const avatarChar = computed(() => (username.value || 'U')[0].toUpperCase())

onMounted(async () => {
  try {
    const r = await api.getMe()
    username.value = r.data.full_name || r.data.username
    isAdmin.value = r.data.role === 'admin'
    isViewer.value = r.data.role === 'viewer'
  } catch { /* */ }
})

function logout() { localStorage.removeItem('token'); router.push('/login') }
</script>

<style scoped>
.sidebar {
  position: fixed; left: 0; top: 0; bottom: 0;
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  display: flex; flex-direction: column;
  justify-content: space-between;
  z-index: 100;
  transition: transform 0.35s var(--spring);
}
.sidebar.collapsed:not(.mobile) { transform: translateX(calc(var(--sidebar-width) * -1)); }
.sidebar.mobile { transform: translateX(-100%); box-shadow: none; }
.sidebar.mobile.open { transform: translateX(0); box-shadow: var(--shadow-xl); }

.sidebar-top { display: flex; flex-direction: column; }

.logo-area {
  display: flex; align-items: center; gap: 10px;
  padding: 18px var(--space-md); position: relative;
}
.logo-mark { flex-shrink: 0; }
.logo-text { display: flex; flex-direction: column; min-width: 0; }
.logo-name {
  font-family: var(--font-display); font-size: 16px; font-weight: 700;
  color: #fff; letter-spacing: 0.02em; line-height: 1.2;
}
.logo-sub {
  font-size: 10px; color: var(--sidebar-text); font-weight: 600;
  letter-spacing: 0.04em;
}
.collapse-btn, .close-btn {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  padding: 6px; background: none; border: none; box-shadow: none;
  color: var(--sidebar-text); cursor: pointer; border-radius: var(--radius-sm);
}
.collapse-btn:hover, .close-btn:hover { color: #fff; background: rgba(255,255,255,0.06); box-shadow: none; transform: translateY(-50%) scale(1.1); }

.nav-links { display: flex; flex-direction: column; gap: 2px; padding: var(--space-sm); }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 14px; border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  font-family: var(--font-display); font-size: 14px; font-weight: 500;
  text-decoration: none;
  transition: all 0.2s var(--spring);
}
.nav-item:hover { background: var(--sidebar-hover); color: #fff; text-decoration: none; }
.nav-item.router-link-active { background: var(--sidebar-active); color: #60a5fa; }

.sidebar-bottom { padding: var(--space-sm) var(--space-sm) var(--space-md); position: relative; }
.user-area {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s var(--spring);
}
.user-area:hover { background: var(--sidebar-hover); }
.user-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--color-primary);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 13px; font-weight: 700;
  color: #fff; flex-shrink: 0;
}
.user-info { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.user-name { font-size: 13px; font-weight: 700; color: #fff; }
.user-role { font-size: 11px; color: var(--sidebar-text); font-weight: 500; }
.chevron { color: var(--sidebar-text); flex-shrink: 0; transition: transform 0.3s var(--spring); }
.chevron.open { transform: rotate(180deg); }

.user-dropdown {
  position: absolute; bottom: 100%;
  left: var(--space-sm); right: var(--space-sm);
  background: var(--sidebar-hover); border-radius: var(--radius-md);
  padding: 4px; margin-bottom: 4px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
  animation: popIn 0.2s var(--spring);
}
@keyframes popIn { from { opacity: 0; transform: translateY(8px) scale(0.94); } to { opacity: 1; transform: translateY(0) scale(1); } }
.dropdown-item {
  width: 100%; justify-content: flex-start;
  font-size: 13px; color: #fff; padding: 10px 14px; border-radius: var(--radius-sm);
  background: none; border: none; box-shadow: none;
}
.dropdown-item:hover { background: rgba(255,255,255,0.06); box-shadow: none; transform: none; }

@media (max-width: 768px) {
  .sidebar { width: 280px; }
}
</style>
