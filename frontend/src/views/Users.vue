<template>
  <div class="page">
    <div class="page-header">
      <h2>用户管理</h2>
      <p class="sub">管理系统用户与角色权限</p>
    </div>

    <div class="card create-form">
      <h4>新建用户</h4>
      <div class="form-row">
        <input v-model="form.username" placeholder="用户名" class="fld" />
        <input v-model="form.email" placeholder="邮箱" type="email" class="fld" />
        <input v-model="form.password" placeholder="密码" type="password" class="fld" />
        <select v-model="form.role" class="fld">
          <option value="viewer">查看者</option>
          <option value="editor">编辑者</option>
          <option value="admin">管理员</option>
        </select>
        <button @click="createUser">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          创建
        </button>
      </div>
    </div>

    <div v-if="users.length" class="users-list card">
      <div class="list-header">
        <span class="col col-name">用户</span>
        <span class="col col-role">角色</span>
        <span class="col col-status">状态</span>
        <span class="col col-act">操作</span>
      </div>
      <div v-for="u, idx in users" :key="u.id" class="list-row" :style="{ animationDelay: idx * 0.03 + 's' }">
        <div class="col col-name">
          <div class="u-avatar" :class="'av-' + u.role">{{ (u.full_name || u.username)[0].toUpperCase() }}</div>
          <div class="u-detail">
            <span class="uname">{{ u.full_name || u.username }}</span>
            <span class="uemail">{{ u.email }}</span>
          </div>
        </div>
        <div class="col col-role">
          <span class="badge" :class="'rb-' + u.role">{{ roleLabel(u.role) }}</span>
        </div>
        <div class="col col-status">
          <span class="dot" :class="{ on: u.is_active }" /> {{ u.is_active ? '正常' : '禁用' }}
        </div>
        <div class="col col-act">
          <button class="secondary sm" @click="toggleUser(u)">{{ u.is_active ? '禁用' : '启用' }}</button>
        </div>
      </div>
    </div>
    <div v-else class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
      <p>暂无用户</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'

const users = ref([])
const form = reactive({ username: '', email: '', password: '', role: 'viewer' })

onMounted(async () => { users.value = (await api.listUsers()).data })

async function createUser() {
  if (!form.username || !form.email || !form.password) return alert('请填写完整')
  try {
    await api.createUser(form)
    form.username = form.email = form.password = ''; form.role = 'viewer'
    users.value = (await api.listUsers()).data
  } catch (e) { alert(e.response?.data?.detail || '创建失败') }
}
async function toggleUser(u) {
  await api.updateUser(u.id, { is_active: !u.is_active })
  users.value = (await api.listUsers()).data
}
function roleLabel(r) { return { admin: '管理员', editor: '编辑者', viewer: '查看者' }[r] || r }
</script>

<style scoped>
.page { padding-bottom: var(--space-xl); }
.page-header { margin-bottom: var(--space-lg); }
.page-header h2 { margin-bottom: 4px; }
.sub { color: var(--color-text-secondary); font-size: 14px; }

.create-form { padding: 20px; margin-bottom: var(--space-lg); border: 2px solid var(--color-border); }
.create-form h4 { font-size: 14px; font-weight: 700; color: var(--color-text-secondary); margin-bottom: 14px; font-family: var(--font-display); }
.form-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.fld { width: 140px; }

.users-list { padding: 0; overflow: hidden; border: 2px solid var(--color-border); border-radius: var(--radius-lg); }
.list-header {
  display: flex; align-items: center;
  padding: 10px 20px; background: var(--color-bg);
  border-bottom: 2px solid var(--color-border);
  font-size: 11px; font-weight: 700; color: var(--color-text-muted);
  text-transform: uppercase; letter-spacing: 0.04em; font-family: var(--font-display);
}
.list-row {
  display: flex; align-items: center; padding: 14px 20px;
  border-bottom: 1px solid var(--color-border-light);
  transition: all 0.2s var(--spring);
  animation: rowIn 0.3s var(--spring) both;
}
.list-row:last-child { border-bottom: none; }
.list-row:hover { background: var(--color-surface-hover); transform: translateX(3px); }
@keyframes rowIn { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: translateX(0); } }

.col-name { flex: 1; min-width: 0; display: flex; align-items: center; gap: 10px; }
.col-role { width: 100px; }
.col-status { width: 90px; }
.col-act { width: 80px; text-align: right; }

.u-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 13px; font-weight: 700;
  color: #fff; flex-shrink: 0;
}
.av-admin  { background: var(--color-purple); }
.av-editor { background: var(--color-primary); }
.av-viewer { background: var(--color-text-muted); }

.u-detail { display: flex; flex-direction: column; min-width: 0; }
.uname { font-size: 14px; font-weight: 700; }
.uemail { font-size: 12px; color: var(--color-text-muted); font-weight: 600; }

.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--color-danger); display: inline-block; margin-right: 5px; }
.dot.on { background: var(--color-success); }

.badge.rb-admin  { background: rgba(124,58,237,0.1); color: var(--color-purple); }
.badge.rb-editor { background: var(--color-primary-subtle); color: var(--color-primary); }
.badge.rb-viewer { background: var(--color-bg); color: var(--color-text-secondary); }

.empty { text-align: center; padding: 100px 0; color: var(--color-text-muted); }
.empty p { margin-top: 12px; font-size: 14px; font-weight: 600; }

@media (max-width: 640px) {
  .list-header { display: none; }
  .list-row { flex-direction: column; align-items: flex-start; gap: 8px; padding: 14px; }
  .col-role, .col-status, .col-act { width: auto; }
  .col-act { align-self: flex-end; margin-top: -32px; }
  .form-row { flex-direction: column; }
  .fld { width: 100%; }
}
</style>
