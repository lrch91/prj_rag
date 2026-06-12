<template>
  <div class="app" :class="{ 'sidebar-open': sidebarOpen, 'sidebar-collapsed': !sidebarOpen && isLoggedIn }">
    <div v-if="sidebarOpen && isMobile" class="sidebar-overlay" @click="closeSidebar" />

    <Sidebar
      v-if="isLoggedIn"
      :collapsed="!sidebarOpen"
      :is-mobile="isMobile"
      @toggle="toggleSidebar"
      @close="closeSidebar"
    />

    <button v-if="isLoggedIn && !isMobile && !sidebarOpen" class="sidebar-toggle-btn" @click="toggleSidebar">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
    </button>

    <main class="main">
      <header v-if="isLoggedIn && isMobile" class="mobile-header">
        <button class="menu-btn" @click="openSidebar">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
        <span class="mobile-title">KnowledgeBase</span>
      </header>
      <div class="main-inner">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
    <Transition name="toast">
      <div v-if="errMsg" class="error-toast" @click="errMsg = ''">{{ errMsg }}</div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from './components/Sidebar.vue'

const router = useRouter()
const sidebarOpen = ref(true)
const isMobile = ref(false)
const errMsg = ref('')
const isLoggedIn = ref(!!localStorage.getItem('token'))

// localStorage 非响应式，路由变化时重新检查登录状态
watch(() => router.currentRoute.value, () => {
  isLoggedIn.value = !!localStorage.getItem('token')
})

function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) sidebarOpen.value = false
  else sidebarOpen.value = true
}
let errTimer = 0
onMounted(() => {
  checkMobile(); window.addEventListener('resize', checkMobile)
  window.addEventListener('app-error', e => {
    errMsg.value = e.detail; clearTimeout(errTimer)
    errTimer = setTimeout(() => errMsg.value = '', 5000)
  })
})
onUnmounted(() => { window.removeEventListener('resize', checkMobile); clearTimeout(errTimer) })

function toggleSidebar() { sidebarOpen.value = !sidebarOpen.value }
function openSidebar() { sidebarOpen.value = true }
function closeSidebar() { sidebarOpen.value = false }
</script>

<style>
/* ═══════════════ FRESH TOY — High Contrast Playful ═══════════════ */
:root {
  --color-bg:            #f8fafc;
  --color-surface:       #ffffff;
  --color-surface-hover: #f1f5f9;
  --color-surface-raised:#ffffff;

  --color-text:          #0f172a;
  --color-text-secondary:#475569;
  --color-text-muted:    #94a3b8;

  --color-blue:          #2563eb;
  --color-coral:         #e11d48;
  --color-mint:          #059669;
  --color-amber:         #d97706;
  --color-purple:        #7c3aed;

  --color-primary:       #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-subtle:rgba(37,99,235,0.08);
  --color-primary-light: rgba(37,99,235,0.14);
  --color-success:       #059669;
  --color-success-bg:    rgba(5,150,105,0.08);
  --color-danger:        #e11d48;
  --color-danger-bg:     rgba(225,29,72,0.08);
  --color-warning:       #d97706;

  --color-border:        #e2e8f0;
  --color-border-light:  #f1f5f9;

  --sidebar-width:       240px;
  --sidebar-bg:          #0f172a;
  --sidebar-hover:       #1e293b;
  --sidebar-active:      rgba(37,99,235,0.15);
  --sidebar-text:        #94a3b8;
  --sidebar-text-active: #ffffff;

  --font-display: 'Fredoka', 'Noto Sans SC', sans-serif;
  --font-body:    'Nunito', 'Noto Sans SC', sans-serif;

  --space-xs:  4px;
  --space-sm:  8px;
  --space-md:  16px;
  --space-lg:  24px;
  --space-xl:  36px;
  --space-2xl: 52px;
  --radius-sm: 10px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-xl: 26px;
  --radius-full: 9999px;

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04);
  --shadow-xl: 0 16px 48px rgba(0,0,0,0.1);

  --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

html { -webkit-font-smoothing: antialiased; background: var(--color-bg); }
body {
  font-family: var(--font-body);
  font-size: 15px; font-weight: 500;
  line-height: 1.55; background: var(--color-bg);
  color: var(--color-text);
}
#app { min-height: 100vh; }

h1, h2, h3, h4 {
  font-family: var(--font-display);
  font-weight: 600; line-height: 1.2; color: var(--color-text);
}
h1 { font-size: 30px; }
h2 { font-size: 23px; }
h3 { font-size: 18px; }
h4 { font-size: 15px; }

a { color: var(--color-primary); text-decoration: none; }
a:hover { text-decoration: underline; }

input, textarea, select {
  font-family: var(--font-body); font-size: 14px; font-weight: 500;
  padding: 10px 14px; border: 2px solid var(--color-border);
  border-radius: var(--radius-sm); background: var(--color-surface);
  color: var(--color-text); outline: none;
  transition: all 0.2s var(--spring);
}
input:focus, textarea:focus, select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-subtle);
}
input::placeholder, textarea::placeholder { color: var(--color-text-muted); }
select {
  cursor: pointer; appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2.5' stroke-linecap='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px;
}

button {
  font-family: var(--font-display); font-size: 14px; font-weight: 600;
  padding: 10px 20px; border: none; border-radius: var(--radius-sm);
  background: var(--color-primary); color: #fff;
  cursor: pointer; display: inline-flex; align-items: center; gap: 7px;
  box-shadow: 0 2px 0 #1e40af, 0 4px 12px rgba(37,99,235,0.2);
  transition: all 0.2s var(--spring);
  white-space: nowrap;
}
button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 0 #1e40af, 0 8px 20px rgba(37,99,235,0.3);
  background: var(--color-primary-hover);
}
button:active { transform: translateY(1px); box-shadow: 0 1px 0 #1e40af; }
button:disabled { opacity: 0.45; cursor: not-allowed; transform: none; box-shadow: none; }

button.coral { background: var(--color-coral); box-shadow: 0 2px 0 #be123c, 0 4px 12px rgba(225,29,72,0.2); }
button.coral:hover { box-shadow: 0 4px 0 #be123c, 0 8px 20px rgba(225,29,72,0.3); background: #be123c; }
button.mint { background: var(--color-mint); box-shadow: 0 2px 0 #047857, 0 4px 12px rgba(5,150,105,0.2); }
button.mint:hover { box-shadow: 0 4px 0 #047857, 0 8px 20px rgba(5,150,105,0.3); background: #047857; }
button.amber { background: var(--color-amber); box-shadow: 0 2px 0 #b45309, 0 4px 12px rgba(217,119,6,0.2); }
button.amber:hover { box-shadow: 0 4px 0 #b45309, 0 8px 20px rgba(217,119,6,0.3); background: #b45309; }

button.ghost {
  background: transparent; color: var(--color-text-secondary); box-shadow: none;
}
button.ghost:hover { background: var(--color-surface-hover); color: var(--color-text); transform: none; box-shadow: none; }
button.ghost.danger:hover { background: var(--color-danger-bg); color: var(--color-danger); }

button.sm { padding: 6px 14px; font-size: 12px; }

.card {
  background: var(--color-surface); border: 2px solid var(--color-border);
  border-radius: var(--radius-lg); padding: var(--space-lg);
  box-shadow: var(--shadow-sm);
  transition: all 0.25s var(--spring);
}
.card:hover { border-color: var(--color-primary); box-shadow: var(--shadow-md); transform: translateY(-2px); }

.badge {
  display: inline-flex; align-items: center; padding: 3px 10px;
  border-radius: var(--radius-full); font-family: var(--font-display);
  font-size: 10px; font-weight: 600;
}

/* ═══════════════ LAYOUT ═══════════════ */
.app { display: flex; min-height: 100vh; background: var(--color-bg); }

.main {
  flex: 1; margin-left: var(--sidebar-width);
  transition: margin-left 0.35s var(--spring);
  display: flex; flex-direction: column; min-height: 100vh;
}
.app.sidebar-collapsed .main { margin-left: 0; }

.sidebar-toggle-btn {
  position: fixed; left: 0; top: 50%; transform: translateY(-50%);
  width: 28px; height: 52px;
  background: var(--color-primary); color: #fff; border: none;
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 80;
  box-shadow: 2px 0 0 #1e40af, 4px 0 16px rgba(37,99,235,0.15);
  transition: all 0.25s var(--spring);
}
.sidebar-toggle-btn:hover { transform: translateY(-50%) scale(1.06); box-shadow: 2px 0 0 #1e40af, 6px 0 24px rgba(37,99,235,0.25); }

.sidebar-overlay {
  position: fixed; inset: 0; background: rgba(15,23,42,0.3);
  z-index: 90; backdrop-filter: blur(4px);
}

.mobile-header {
  display: flex; align-items: center; gap: 12px;
  padding: 12px var(--space-md);
  background: rgba(255,255,255,0.92); backdrop-filter: blur(16px);
  border-bottom: 2px solid var(--color-border-light);
  position: sticky; top: 0; z-index: 50;
}
.menu-btn {
  padding: 8px; background: none; border: none; box-shadow: none;
  color: var(--color-text); cursor: pointer; border-radius: var(--radius-sm);
}
.menu-btn:hover { background: var(--color-surface-hover); box-shadow: none; transform: scale(1.1); }
.mobile-title { font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--color-text); }

.main-inner {
  flex: 1; max-width: 1160px; width: 100%; margin: 0 auto;
  padding: var(--space-xl) var(--space-xl) var(--space-3xl);
}

/* Page Transitions */
.page-enter-active { transition: all 0.35s var(--spring); }
.page-leave-active { transition: all 0.15s ease-in; }
.page-enter-from { opacity: 0; transform: translateY(16px) scale(0.96); }
.page-leave-to { opacity: 0; transform: translateY(-8px) scale(0.98); }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
::selection { background: rgba(37,99,235,0.18); color: var(--color-text); }

@media (max-width: 768px) {
  .main { margin-left: 0 !important; }
  .main-inner { padding: var(--space-md) var(--space-md) var(--space-xl); }
}
@media (min-width: 769px) { .mobile-header { display: none; } }
.error-toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  background: var(--color-danger); color: #fff; padding: 12px 24px;
  border-radius: var(--radius-sm); font-weight: 600; font-size: 14px;
  z-index: 999; cursor: pointer; box-shadow: var(--shadow-lg);
  max-width: 90vw; text-align: center;
}
.toast-enter-active { transition: all 0.3s var(--spring); }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(16px); }
</style>
