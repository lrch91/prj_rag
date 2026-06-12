<template>
  <div class="page">
    <div class="page-header">
      <h2>知识库</h2>
      <p class="sub">管理知识库与文档</p>
    </div>

    <div class="create-bar">
      <input v-model="newName" placeholder="知识库名称" @keydown.enter="create" class="create-input" />
      <button @click="create">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        创建
      </button>
    </div>

    <div v-if="kbs.length" class="kb-grid">
      <div v-for="k, idx in kbs" :key="k.id" class="card kb-card" :style="{ animationDelay: idx * 0.04 + 's' }">
        <div class="kb-main">
          <div class="kb-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          </div>
          <div class="kb-info">
            <strong class="kb-name">{{ k.name }}</strong>
            <p v-if="k.description" class="kb-desc">{{ k.description }}</p>
            <span class="kb-meta">{{ k.created_at?.slice(0, 10) }}</span>
          </div>
        </div>
        <div class="kb-actions">
          <button class="ghost sm" title="权限管理" @click="openPerm(k)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </button>
          <router-link :to="`/kbs/${k.id}/docs`" class="action-link">文档</router-link>
          <button class="ghost danger sm" @click="del(k.id)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
      <p>创建知识库开始使用</p>
    </div>

    <!-- Permission Modal -->
    <Teleport to="body">
      <Transition name="perm-fade">
        <div v-if="permKB" class="perm-overlay" @click.self="permKB = null">
          <div class="perm-panel">
            <div class="perm-hd">
              <span>权限管理 — {{ permKB.name }}</span>
              <button class="perm-close" @click="permKB = null">&times;</button>
            </div>
            <div class="perm-bd">
              <div class="perm-add">
                <select v-model="permUser" class="perm-select">
                  <option value="">选择用户</option>
                  <option v-for="u in allUsers" :key="u.id" :value="u.id">{{ u.username }} ({{ roleLabel(u.role) }})</option>
                </select>
                <select v-model="permRole" class="perm-select">
                  <option value="read">只读</option>
                  <option value="write">读写</option>
                  <option value="admin">管理</option>
                </select>
                <button class="sm mint" @click="grantPerm">添加</button>
              </div>
              <div v-if="perms.length" class="perm-list">
                <div v-for="p in perms" :key="p.user_id" class="perm-row">
                  <span class="perm-user">{{ userMap[p.user_id] || p.user_id }}</span>
                  <span class="badge" :class="'rb-' + p.permission">{{ permLabel(p.permission) }}</span>
                  <button class="ghost sm danger" @click="revokePerm(p.user_id)">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                </div>
              </div>
              <p v-else class="perm-empty">暂无权限配置</p>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const kbs = ref([])
const newName = ref('')
const permKB = ref(null)
const perms = ref([])
const allUsers = ref([])
const permUser = ref('')
const permRole = ref('read')
const userMap = ref({})

onMounted(async () => { kbs.value = (await api.listKBs()).data })

async function openPerm(k) {
  permKB.value = k; permUser.value = ''; permRole.value = 'read'
  try {
    const [pr, ur] = await Promise.all([api.listKBPerms(k.id), api.listUsers()])
    perms.value = pr.data
    allUsers.value = ur.data
    userMap.value = {}
    ur.data.forEach(u => userMap.value[u.id] = u.full_name || u.username)
  } catch { perms.value = []; allUsers.value = [] }
}
async function grantPerm() {
  if (!permUser.value || !permKB.value) return
  try {
    await api.grantKB(permKB.value.id, permUser.value, permRole.value)
    const pr = await api.listKBPerms(permKB.value.id)
    perms.value = pr.data
    permUser.value = ''
  } catch (e) { alert(e.response?.data?.detail || '添加失败') }
}
async function revokePerm(uid) {
  if (!permKB.value) return
  try {
    await api.revokeKB(permKB.value.id, uid)
    perms.value = (await api.listKBPerms(permKB.value.id)).data
  } catch { /* */ }
}
async function create() {
  if (!newName.value.trim()) return
  await api.createKB({ name: newName.value })
  newName.value = ''; kbs.value = (await api.listKBs()).data
}
async function del(id) {
  if (!confirm('确定删除？')) return
  try { await api.deleteKB(id); kbs.value = (await api.listKBs()).data }
  catch (e) { alert(e.response?.data?.detail || '删除失败') }
}
function roleLabel(r) { return { admin:'管理员', editor:'编辑者', viewer:'查看者' }[r] || r }
function permLabel(p) { return { read:'只读', write:'读写', admin:'管理' }[p] || p }
</script>

<style scoped>
.page { padding-bottom: var(--space-xl); }
.page-header { margin-bottom: var(--space-lg); }
.page-header h2 { margin-bottom: 4px; }
.sub { color: var(--color-text-secondary); font-size: 14px; }
.create-bar { display: flex; gap: 8px; margin-bottom: var(--space-lg); }
.create-input { width: 260px; }
.kb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: var(--space-sm); }
.kb-card { display: flex; justify-content: space-between; align-items: center; padding: 18px 20px; border: 2px solid var(--color-border); animation: cardIn 0.35s var(--spring) both; }
@keyframes cardIn { from { opacity: 0; transform: translateY(8px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
.kb-main { display: flex; gap: 14px; align-items: flex-start; min-width: 0; }
.kb-icon { width: 42px; height: 42px; border-radius: var(--radius-sm); background: var(--color-primary-subtle); color: var(--color-primary); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kb-info { min-width: 0; }
.kb-name { font-size: 16px; font-weight: 700; display: block; margin-bottom: 2px; font-family: var(--font-display); }
.kb-desc { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 600; }
.kb-meta { font-size: 12px; color: var(--color-text-muted); font-weight: 600; }
.kb-actions { display: flex; gap: 6px; align-items: center; flex-shrink: 0; }
.action-link { display: inline-flex; align-items: center; gap: 5px; font-size: 13px; font-weight: 700; color: var(--color-primary); padding: 7px 14px; border-radius: var(--radius-full); transition: all 0.2s var(--spring); }
.action-link:hover { background: var(--color-primary-subtle); text-decoration: none; }
.empty { text-align: center; padding: 100px 0; color: var(--color-text-muted); }
.empty p { margin-top: 12px; font-size: 14px; font-weight: 600; }

/* Permission Modal */
.perm-overlay { position: fixed; inset: 0; z-index: 100; background: rgba(15,23,42,0.3); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; padding: 24px; }
.perm-fade-enter-active, .perm-fade-leave-active { transition: all 0.2s var(--spring); }
.perm-fade-enter-from, .perm-fade-leave-to { opacity: 0; }
.perm-fade-enter-from .perm-panel, .perm-fade-leave-to .perm-panel { transform: scale(0.95); }
.perm-panel { width: 100%; max-width: 500px; background: var(--color-surface); border: 2px solid var(--color-border); border-radius: var(--radius-xl); box-shadow: var(--shadow-xl); overflow: hidden; transition: transform 0.2s var(--spring); }
.perm-hd { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 2px solid var(--color-border); font-size: 15px; font-weight: 700; font-family: var(--font-display); }
.perm-close { width: 36px; height: 36px; border: 2px solid var(--color-border); background: var(--color-bg); border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--color-text); font-size: 22px; font-weight: 700; line-height: 1; }
.perm-close:hover { background: var(--color-danger-bg); border-color: var(--color-danger); color: var(--color-danger); }
.perm-bd { padding: 16px 20px 20px; }
.perm-add { display: flex; gap: 8px; margin-bottom: 14px; }
.perm-select { flex: 1; font-size: 13px; }
.perm-list { display: flex; flex-direction: column; gap: 4px; }
.perm-row { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: var(--radius-sm); background: var(--color-bg); }
.perm-user { flex: 1; font-size: 14px; font-weight: 600; }
.perm-empty { text-align: center; color: var(--color-text-muted); font-size: 13px; padding: 20px 0; }

.badge.rb-read  { background: var(--color-success-bg); color: var(--color-success); }
.badge.rb-write { background: var(--color-primary-subtle); color: var(--color-primary); }
.badge.rb-admin { background: rgba(124,58,237,0.1); color: var(--color-purple); }

@media (max-width: 480px) {
  .kb-grid { grid-template-columns: 1fr; }
  .create-bar { flex-direction: column; }
  .create-input { width: 100%; }
  .perm-add { flex-direction: column; }
}
</style>
