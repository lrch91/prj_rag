<template>
  <div class="chat-layout">
    <!-- Conversation Panel -->
    <div class="conv-panel" :class="{ open: convPanelOpen }">
      <div class="conv-panel-header">
        <span class="conv-panel-title">对话</span>
        <button class="ghost sm" @click="convPanelOpen = false">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <button class="new-conv-btn" @click="newChat">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新对话
      </button>
      <div class="conv-list">
        <div v-for="c in convs" :key="c.id" class="conv-item" :class="{ active: c.id === convId }" @click="openChat(c.id)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="conv-title">{{ c.title || '新对话' }}</span>
          <button class="conv-del" @click.stop="delConv(c.id)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <p v-if="!convs.length" class="empty-conv">暂无对话</p>
      </div>
    </div>
    <div v-if="convPanelOpen && isMobile" class="conv-overlay" @click="convPanelOpen = false" />

    <!-- Main Chat -->
    <div class="chat-main">
      <div class="chat-topbar">
        <button class="ghost sm conv-toggle" @click="convPanelOpen = !convPanelOpen">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
        </button>
        <div class="config-inline">
          <select v-model="selectedKB" class="kb-select">
            <option value="">全部知识库</option>
            <option v-for="k in kbs" :key="k.id" :value="k.id">{{ k.name }}</option>
          </select>
          <select v-model="model" class="model-select">
            <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </div>
      </div>

      <div class="messages-panel" ref="msgBox">
        <div v-if="!messages.length && !loading" class="welcome">
          <div class="welcome-icon">
            <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
              <rect width="56" height="56" rx="16" fill="url(#wgrad)"/>
              <path d="M16 24h24M16 32h19M17 19l-2 5v15a2 2 0 002 2h22a2 2 0 002-2V24l-2-5H17z" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              <defs><linearGradient id="wgrad" x1="0" y1="0" x2="56" y2="56"><stop stop-color="#0071e3"/><stop offset="1" stop-color="#5e5ce6"/></linearGradient></defs>
            </svg>
          </div>
          <h2>有什么可以帮助你的？</h2>
          <p>选择知识库，输入问题开始检索问答</p>
        </div>

        <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
          <div class="msg-avatar">
            <div v-if="m.role === 'user'" class="avatar user-av">{{ (username || 'U')[0].toUpperCase() }}</div>
            <div v-else class="avatar ai-av">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
          </div>
          <div class="msg-body">
            <div class="msg-role">{{ m.role === 'user' ? '你' : 'AI 助手' }}<span class="msg-time">{{ m.time }}</span></div>
            <div class="msg-content" v-html="renderMd(m.content)" />
            <div v-if="m.citations?.length" class="citations">
              <span class="cite-label">引用</span>
              <span v-for="c in m.citations" :key="c.source_index" class="cite-badge" @click="showCite(c)">#{{ c.source_index }}</span>
            </div>
          </div>
        </div>

        <div v-if="loading" class="msg assistant">
          <div class="msg-avatar"><div class="avatar ai-av"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div></div>
          <div class="msg-body">
            <div class="msg-role">AI 助手</div>
            <div class="typing-indicator"><span /><span /><span /></div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <textarea v-model="question" @keydown.enter.exact.prevent="send" placeholder="输入问题，Enter 发送..." rows="1" class="chat-input" />
        <button class="send-btn" @click="send" :disabled="!question.trim() || loading">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>

    <!-- Citation Detail Overlay -->
    <Teleport to="body">
      <Transition name="cite-fade">
        <div v-if="citeDetail" class="cite-overlay" @click.self="citeDetail = null">
          <div class="cite-panel">
            <div class="cite-panel-hd">
              <div class="cite-panel-label">来源 #{{ citeDetail.source_index }}</div>
              <button class="cite-panel-close" @click="citeDetail = null">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div class="cite-panel-bd">
              <div class="cite-meta">
                <div class="cite-meta-item" v-if="citeDetail.kb_name">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                  <span>{{ citeDetail.kb_name }}</span>
                </div>
                <div class="cite-meta-item" v-if="citeDetail.document_title">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  <span>{{ citeDetail.document_title }}</span>
                  <span class="cite-meta-page" v-if="citeDetail.page">第 {{ citeDetail.page }} 页</span>
                </div>
                <div class="cite-meta-item cite-section" v-if="citeDetail.section_path">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                  <span>{{ citeDetail.section_path }}</span>
                </div>
              </div>
              <div class="cite-score">
                <div class="cite-score-bar"><div class="cite-score-fill" :style="{ width: ((citeDetail.relevance_score || 0) * 100).toFixed(2) + '%' }" /></div>
                <span>相关度 {{ ((citeDetail.relevance_score || 0) * 100).toFixed(8) }}%</span>
              </div>
              <div class="cite-snippet">{{ citeDetail.snippet }}</div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import api from '../api'

const md = new MarkdownIt({ breaks: true, linkify: true })
const kbs = ref([])
const convs = ref([])
const convId = ref(null)
const selectedKB = ref('')
const models = ref([{ id: 'deepseek-v4-pro', name: 'DeepSeek V4-Pro' }])
const model = ref('deepseek-v4-pro')
const question = ref('')
const messages = ref([])
const loading = ref(false)
const msgBox = ref(null)
const username = ref('')
const convPanelOpen = ref(false)
const isMobile = ref(false)

onMounted(async () => {
  isMobile.value = window.innerWidth < 768
  try {
    const [kbRes, convRes, meRes, modelRes] = await Promise.all([api.listKBs(), api.listConvs(), api.getMe(), api.listModels()])
    kbs.value = kbRes.data; convs.value = convRes.data
    username.value = meRes.data.full_name || meRes.data.username
    models.value = modelRes.data.models
    model.value = modelRes.data.default || 'deepseek-v4-pro'
  } catch { /* */ }
})

async function newChat() { convId.value = null; messages.value = []; convPanelOpen.value = false }
async function openChat(id) {
  convId.value = id
  try { const r = await api.getConv(id); messages.value = r.data.messages.map(m => ({ role: m.role, content: m.content, citations: m.citations, time: _fmtTime(m.created_at) })) } catch { /* */ }
  convPanelOpen.value = false; scrollDown()
}
async function delConv(id) {
  try { await api.delConv(id) } catch { /* */ }
  if (convId.value === id) { convId.value = null; messages.value = [] }
  try { const r = await api.listConvs(); convs.value = r.data } catch { /* */ }
}
function aiMsg() { return messages.value[messages.value.length - 1] }
function _now() { return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
function _fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso + 'Z')
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function send() {
  if (!question.value.trim() || loading.value) return
  const q = question.value
  messages.value.push({ role: 'user', content: q, time: _now() })
  question.value = ''
  loading.value = true
  scrollDown()

  let started = false

  try {
    const token = localStorage.getItem('token')
    const resp = await fetch('/api/v1/qa/ask/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ question: q, kb_ids: selectedKB.value ? [selectedKB.value] : [], model: model.value, conversation_id: convId.value }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const p = JSON.parse(line.slice(6))
          if (p.token) {
            if (!started) {
              loading.value = false
              messages.value.push({ role: 'assistant', content: '', citations: [], time: _now() })
              started = true
            }
            aiMsg().content += p.token
          } else if (p.done) {
            if (!started) {
              loading.value = false
              messages.value.push({ role: 'assistant', content: '', citations: [], time: _now() })
              started = true
            }
            aiMsg().citations = p.citations || []
            if (p.conversation_id) convId.value = p.conversation_id
            await nextTick()
          } else if (p.error) {
            if (!started) {
              loading.value = false
              messages.value.push({ role: 'assistant', content: '', citations: [], time: _now() })
              started = true
            }
            aiMsg().content = '请求失败: ' + p.error
          }
        } catch {}
      }
      scrollDown()
    }
    if (!started) {
      loading.value = false
      messages.value.push({ role: 'assistant', content: '(空响应)', citations: [], time: _now() })
    }
    // Refresh conversation list
    if (convId.value) {
      try { const cr = await api.listConvs(); convs.value = cr.data } catch {}
    }
  } catch (e) {
    loading.value = false
    if (!started) messages.value.push({ role: 'assistant', content: '请求失败: ' + (e.message || '未知错误'), citations: [], time: _now() })
  }
  loading.value = false
  scrollDown()
}
function scrollDown() { nextTick(() => { if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight }) }
function renderMd(text) { return md.render(text || '') }
const citeDetail = ref(null)
function showCite(c) { citeDetail.value = c }
</script>

<style scoped>
.chat-layout {
  display: flex; height: calc(100vh - var(--space-xl) * 2);
  border-radius: var(--radius-xl); overflow: hidden;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-md);
}

/* Conv Panel */
.conv-panel {
  width: 240px; flex-shrink: 0;
  border-right: 2px solid var(--color-border);
  display: flex; flex-direction: column;
  background: var(--color-bg);
}
.conv-panel-header { display: none; align-items: center; justify-content: space-between; padding: 10px 12px; border-bottom: 2px solid var(--color-border); }
.conv-panel-title { font-weight: 700; font-size: 14px; font-family: var(--font-display); }

.new-conv-btn {
  margin: 10px; justify-content: center; height: 38px;
  font-size: 13px; font-weight: 700;
  background: var(--color-surface); color: var(--color-primary);
  border: 2px solid var(--color-border); box-shadow: none;
}
.new-conv-btn:hover { background: var(--color-primary-subtle); border-color: var(--color-primary); box-shadow: none; }

.conv-list { flex: 1; overflow-y: auto; padding: 0 8px 8px; }
.conv-item {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 10px; border-radius: var(--radius-sm);
  cursor: pointer; font-size: 13px; color: var(--color-text-secondary);
  transition: all 0.2s var(--spring); font-weight: 600;
}
.conv-item:hover { background: var(--color-surface-hover); color: var(--color-text); transform: translateX(3px); }
.conv-item.active { background: var(--color-primary-subtle); color: var(--color-primary); font-weight: 700; }
.conv-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.conv-del {
  display: flex; width: 24px; height: 24px; padding: 0; border: none; background: none; box-shadow: none;
  border-radius: 50%; cursor: pointer; color: var(--color-text-muted); flex-shrink: 0;
  align-items: center; justify-content: center; opacity: 0;
  transition: opacity 0.2s;
}
.conv-item:hover .conv-del, .conv-del:focus-visible { opacity: 1; }
.conv-del:hover { background: var(--color-danger-bg); color: var(--color-danger); box-shadow: none; opacity: 1; }
@media (hover: none) { .conv-del { opacity: 0.5; } }
.empty-conv { padding: 20px 10px; text-align: center; color: var(--color-text-muted); font-size: 12px; }

/* Chat Main */
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.chat-topbar {
  padding: 10px 16px; border-bottom: 2px solid var(--color-border);
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.conv-toggle { padding: 4px; display: none; }
.config-inline { display: flex; align-items: center; gap: 10px; flex: 1; flex-wrap: wrap; }

.kb-select, .model-select { height: 32px; font-size: 12px; padding: 2px 28px 2px 12px; border-radius: var(--radius-full); max-width: 180px; }

/* Messages */
.messages-panel { flex: 1; overflow-y: auto; padding: 24px; }

.welcome { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; color: var(--color-text-secondary); }
.welcome-icon { margin-bottom: 16px; }
.welcome h2 { font-size: 22px; color: var(--color-text); margin-bottom: 4px; }
.welcome p { font-size: 14px; }

.msg { display: flex; gap: 12px; margin-bottom: 24px; animation: msgIn 0.35s var(--spring); }
@keyframes msgIn { from { opacity: 0; transform: translateY(10px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }
.msg-avatar { flex-shrink: 0; }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-size: 13px; font-weight: 700; }
.user-av { background: var(--color-primary); color: #fff; }
.ai-av { background: var(--color-mint); color: #fff; }
.msg-body { min-width: 0; }
.msg-role { font-size: 12px; font-weight: 700; color: var(--color-text-muted); margin-bottom: 4px; font-family: var(--font-display); }
.msg-time { font-weight: 500; font-size: 11px; color: var(--color-text-muted); margin-left: 8px; opacity: 0.65; }
.msg-content { font-size: 15px; line-height: 1.7; color: var(--color-text); }
.msg-content :deep(pre) { background: var(--color-bg); padding: 14px; border-radius: var(--radius-md); overflow-x: auto; font-size: 13px; line-height: 1.5; }
.msg-content :deep(code) { background: var(--color-bg); padding: 2px 6px; border-radius: 4px; font-size: 13px; color: var(--color-coral); font-weight: 600; }
.msg-content :deep(pre code) { background: transparent; color: var(--color-text); padding: 0; }
.msg-content :deep(p) { margin-bottom: 8px; }
.msg-content :deep(ul), .msg-content :deep(ol) { padding-left: 20px; margin-bottom: 8px; }
.msg-content :deep(blockquote) { border-left: 3px solid var(--color-primary); padding-left: 14px; color: var(--color-text-secondary); margin: 8px 0; }

.citations { margin-top: 8px; display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.cite-label { font-size: 11px; color: var(--color-text-muted); font-weight: 600; }
.cite-badge {
  padding: 2px 10px; border-radius: var(--radius-full);
  background: var(--color-primary-subtle); color: var(--color-primary);
  font-size: 11px; font-weight: 700; cursor: pointer;
  transition: all 0.2s var(--spring);
}
.cite-badge:hover { background: var(--color-primary); color: #fff; transform: scale(1.1); }

.typing-indicator { display: flex; gap: 5px; padding: 6px 0; }
.typing-indicator span { width: 7px; height: 7px; border-radius: 50%; background: var(--color-primary); animation: dotBounce 1.2s ease-in-out infinite; }
.typing-indicator span:nth-child(2) { animation-delay: 0.15s; background: var(--color-coral); }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; background: var(--color-mint); }
@keyframes dotBounce { 0%,60%,100%{transform:translateY(0);opacity:0.3}30%{transform:translateY(-6px);opacity:1} }

.input-area { padding: 16px; border-top: 2px solid var(--color-border); display: flex; gap: 10px; align-items: flex-end; }
.chat-input { flex: 1; resize: none; padding: 12px 18px; border-radius: var(--radius-full); min-height: 44px; max-height: 120px; font-size: 14px; }
.send-btn { width: 44px; height: 44px; padding: 0; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

@media (max-width: 768px) {
  .chat-layout { height: calc(100vh - 48px); border-radius: 0; border: none; }
  .conv-panel { position: fixed; inset: 0; z-index: 60; width: auto; transform: translateX(-100%); transition: transform 0.35s var(--spring); }
  .conv-panel.open { transform: translateX(0); box-shadow: var(--shadow-xl); }
  .conv-panel-header { display: flex; }
  .conv-overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.3); z-index: 55; }
  .conv-toggle { display: flex; }
  .chat-topbar { padding: 8px 10px; }
  .messages-panel { padding: 16px; }
  .input-area { padding: 12px; }
}

/* Citation overlay */
.cite-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(15,23,42,0.3);
  backdrop-filter: blur(6px);
  display: flex; align-items: flex-end; justify-content: center;
  padding: 40px 20px 20px;
}
.cite-fade-enter-active, .cite-fade-leave-active { transition: all 0.3s var(--spring); }
.cite-fade-enter-from, .cite-fade-leave-to { opacity: 0; }
.cite-fade-enter-from .cite-panel, .cite-fade-leave-to .cite-panel { transform: translateY(30px) scale(0.96); }

.cite-panel {
  width: 100%; max-width: 640px; max-height: 70vh;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  display: flex; flex-direction: column; overflow: hidden;
  transition: transform 0.3s var(--spring);
}
.cite-panel-hd {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 2px solid var(--color-border);
}
.cite-panel-label { font-size: 14px; font-weight: 700; color: var(--color-text); font-family: var(--font-display); }
.cite-panel-close {
  width: 32px; height: 32px; padding: 0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-bg); border: none; color: var(--color-text-secondary); cursor: pointer;
  box-shadow: none;
}
.cite-panel-close:hover { background: var(--color-danger-bg); color: var(--color-danger); box-shadow: none; }
.cite-panel-bd { padding: 20px; overflow-y: auto; }
.cite-meta {
  display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px;
  padding: 12px 14px; background: var(--color-bg);
  border-radius: var(--radius-md);
}
.cite-meta-item {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--color-text-secondary); font-weight: 600;
}
.cite-section { font-family: var(--font-display); color: var(--color-primary); font-weight: 600; }
.cite-meta-page {
  font-size: 11px; color: var(--color-text-muted); font-weight: 600;
  background: var(--color-surface); padding: 2px 10px;
  border-radius: var(--radius-full); margin-left: 6px;
  border: 2px solid var(--color-border);
}
.cite-score {
  display: flex; align-items: center; gap: 10px; margin-bottom: 18px;
  font-size: 12px; color: var(--color-text-secondary); font-weight: 600;
}
.cite-score-bar { width: 100px; height: 5px; border-radius: 3px; background: var(--color-border); overflow: hidden; }
.cite-score-fill {
  height: 100%; border-radius: 3px;
  background: var(--color-primary);
}
.cite-snippet { font-size: 14px; line-height: 1.8; color: var(--color-text); white-space: pre-wrap; word-break: break-word; }

@media (max-width: 768px) {
  .cite-overlay { padding: 16px; align-items: center; }
  .cite-panel { max-height: 80vh; }
}
</style>
