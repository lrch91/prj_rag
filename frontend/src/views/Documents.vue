<template>
  <div class="page">
    <div class="page-header">
      <h2>文档管理</h2>
      <p class="sub">上传文档，自动解析分块并建立索引</p>
    </div>

    <div class="upload-bar">
      <input type="file" @change="uploadFile" ref="fileInput" accept=".pdf,.docx,.md,.txt" multiple hidden />
      <button @click="$refs.fileInput.click()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        上传文档
      </button>
      <span class="upload-hint">PDF · DOCX · MD · TXT</span>
    </div>

    <div v-if="uploading" class="uploading card">上传处理中...</div>
    <div v-if="uploadErr" class="upload-err card">{{ uploadErr }}</div>

    <div v-if="docs.length" class="doc-list">
      <div v-for="d, idx in docs" :key="d.id" class="card doc-card" :style="{ animationDelay: idx * 0.03 + 's' }">
        <div class="doc-main">
          <div class="doc-info">
            <div class="doc-title-row">
              <strong>{{ d.title }}</strong>
            </div>
            <div class="doc-meta">
              <span v-if="d.page_count">{{ d.page_count }} 页 · </span>
              <span v-if="d.version > 1" class="doc-version">v{{ d.version }}</span>
              {{ formatSize(d.file_size_bytes) }} · {{ d.created_at?.slice(0, 16) }}
              <span v-if="d.error_message" class="doc-err">{{ d.error_message }}</span>
            </div>
          </div>
        </div>
        <div class="doc-actions">
          <div class="doc-status">
            <span class="doc-status-icon" :class="'s-' + d.status">
              <svg v-if="d.status === 'ready'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              <svg v-else-if="d.status === 'error'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            </span>
            <span class="badge" :class="'s-' + d.status">{{ statusLabel(d.status) }}</span>
          </div>
          <input type="file" :ref="el => updateInputs[d.id] = el" @change="e => updateFile(d.id, e)" accept=".pdf,.docx,.md,.txt" hidden />
          <button v-if="d.status === 'ready'" class="ghost sm" title="上传新版本" @click="updateInputs[d.id]?.click()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          </button>
          <button v-if="d.status === 'ready' && (!d.file_size_bytes || d.file_size_bytes < 52428800)"
            class="ghost sm" title="预览原文档" @click="preview(d)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
          <button class="ghost danger sm" @click="del(d.id)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="!uploading" class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      <p>上传文档开始构建知识库</p>
    </div>

    <!-- Preview Modal -->
    <Teleport to="body">
      <Transition name="prev-fade">
        <div v-if="previewDoc" class="prev-overlay" @click.self="previewDoc = null">
          <div class="prev-panel">
            <div class="prev-hd">
              <span>{{ previewDoc.title }}</span>
              <button class="prev-close" @click="previewDoc = null">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div class="prev-bd">
              <div v-if="prevLoading" class="prev-loading">加载中...</div>
              <iframe v-else-if="prevIsPdf" :src="prevUrl" class="prev-iframe" />
              <div v-else-if="prevHtml" class="prev-html" v-html="prevHtml" />
              <pre v-else class="prev-text">{{ prevContent }}</pre>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()
const kbId = route.params.kbId
const docs = ref([])
const uploading = ref(false)
const uploadErr = ref('')
const updateInputs = ref({})
const previewDoc = ref(null)
const prevContent = ref('')
const prevHtml = ref('')
const prevIsPdf = ref(false)
const prevUrl = ref('')
const prevLoading = ref(false)

onMounted(async () => { docs.value = (await api.listDocs(kbId)).data })

async function preview(d) {
  previewDoc.value = d
  prevContent.value = ''
  prevHtml.value = ''
  prevIsPdf.value = false
  prevUrl.value = ''
  prevLoading.value = true

  const token = localStorage.getItem('token')
  const url = `/api/v1/kbs/${kbId}/documents/${d.id}/file?token=${encodeURIComponent(token)}`
  const ft = d.file_type

  if (ft === 'application/pdf') {
    prevUrl.value = url
    prevIsPdf.value = true
    prevLoading.value = false
    return
  }

  try {
    const resp = await fetch(url)
    if (!resp.ok) throw new Error('加载失败')

    if (ft.includes('wordprocessingml')) {
      const mammoth = await import('mammoth')
      const buf = await resp.arrayBuffer()
      const result = await mammoth.convertToHtml({ arrayBuffer: buf })
      prevHtml.value = result.value
    } else if (ft === 'text/markdown') {
      const MarkdownIt = (await import('markdown-it')).default
      const md = new MarkdownIt({ breaks: true, linkify: true })
      prevHtml.value = md.render(await resp.text())
    } else {
      prevContent.value = await resp.text()
    }
  } catch (e) {
    prevContent.value = '预览失败: ' + (e.message || '')
  }
  prevLoading.value = false
}

async function uploadFile(e) {
  const files = e.target.files; if (!files.length) return
  uploadErr.value = ''
  uploading.value = true
  for (const f of files) {
    try {
      const fd = new FormData(); fd.append('file', f)
      await api.uploadDoc(kbId, fd)
    } catch (e) {
      uploadErr.value = e.response?.data?.detail || '上传失败'
    }
  }
  e.target.value = ''
  docs.value = (await api.listDocs(kbId)).data
  for (let i = 0; i < 10; i++) {
    if (docs.value.every(d => d.status === 'ready' || d.status === 'error')) break
    await new Promise(r => setTimeout(r, 3000))
    docs.value = (await api.listDocs(kbId)).data
  }
  uploading.value = false
}
async function updateFile(docId, e) {
  const file = e.target.files?.[0]; if (!file) return
  uploading.value = true
  try {
    const fd = new FormData(); fd.append('file', file)
    await api.updateDoc(kbId, docId, fd)
    // Poll until ready
    for (let i = 0; i < 20; i++) {
      await new Promise(r => setTimeout(r, 3000))
      docs.value = (await api.listDocs(kbId)).data
      const d = docs.value.find(x => x.id === docId)
      if (d && (d.status === 'ready' || d.status === 'error')) break
    }
  } catch (e) { alert('更新失败: ' + (e.response?.data?.detail || e.message)) }
  uploading.value = false
  e.target.value = ''
}
async function del(id) {
  if (!confirm('确定删除？')) return
  await api.deleteDoc(kbId, id); docs.value = (await api.listDocs(kbId)).data
}
function formatSize(b) { if(!b)return'';if(b<1024)return b+'B';if(b<1048576)return(b/1024).toFixed(1)+'KB';return(b/1048576).toFixed(1)+'MB' }
function statusLabel(s) { const m={ready:'就绪',error:'失败',pending:'等待',parsing:'解析中',indexing:'索引中'}; return m[s]||s }
</script>

<style scoped>
.page { padding-bottom: var(--space-xl); }
.page-header { margin-bottom: var(--space-lg); }
.page-header h2 { margin-bottom: 4px; }
.sub { color: var(--color-text-secondary); font-size: 14px; }

.upload-bar { display: flex; align-items: center; gap: 10px; margin-bottom: var(--space-lg); flex-wrap: wrap; }
.upload-hint { font-size: 12px; color: var(--color-text-muted); font-weight: 600; }

.uploading { color: var(--color-primary); font-size: 14px; font-weight: 700; margin-bottom: var(--space-md); }
.upload-err {
  color: var(--color-danger); font-size: 13px; font-weight: 600;
  margin-bottom: var(--space-md); padding: 10px 16px;
  border: 2px solid var(--color-danger); background: var(--color-danger-bg);
}

.doc-list { display: flex; flex-direction: column; gap: var(--space-xs); }

.doc-card {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 18px; border: 2px solid var(--color-border);
  animation: cardIn 0.35s var(--spring) both;
}
@keyframes cardIn { from { opacity: 0; transform: translateY(6px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }

.doc-main { display: flex; gap: 12px; align-items: center; min-width: 0; }
.doc-info { min-width: 0; }
.doc-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; font-size: 14px; }
.doc-meta { font-size: 12px; color: var(--color-text-muted); font-weight: 600; }
.doc-version {
  display: inline-block; padding: 1px 8px; border-radius: var(--radius-full);
  background: var(--color-primary-subtle); color: var(--color-primary);
  font-size: 10px; font-weight: 700; margin-right: 4px;
}
.doc-err { color: var(--color-danger); margin-left: 6px; font-weight: 600; }
.doc-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.doc-status { display: flex; align-items: center; gap: 5px; }
.doc-status-icon {
  width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.doc-status-icon.s-ready  { color: var(--color-success); }
.doc-status-icon.s-error  { color: var(--color-danger); }
.doc-status-icon.s-pending,
.doc-status-icon.s-parsing,
.doc-status-icon.s-indexing { color: var(--color-primary); }

.badge.s-ready  { background: var(--color-success-bg); color: var(--color-success); }
.badge.s-error  { background: var(--color-danger-bg); color: var(--color-danger); }
.badge.s-pending, .badge.s-parsing, .badge.s-indexing { background: var(--color-primary-subtle); color: var(--color-primary); }

.empty { text-align: center; padding: 100px 0; color: var(--color-text-muted); }
.empty p { margin-top: 12px; font-size: 14px; font-weight: 600; }

@media (max-width: 640px) {
  .doc-card { flex-direction: column; align-items: flex-start; gap: 8px; }
  .doc-main { width: 100%; }
  .doc-actions { width: 100%; justify-content: space-between; }
  .upload-bar { flex-direction: column; align-items: flex-start; }
}

/* Preview Modal */
.prev-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(15,23,42,0.3);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  padding: 32px;
}
.prev-fade-enter-active, .prev-fade-leave-active { transition: all 0.25s var(--spring); }
.prev-fade-enter-from, .prev-fade-leave-to { opacity: 0; }
.prev-fade-enter-from .prev-panel, .prev-fade-leave-to .prev-panel { transform: scale(0.94); }

.prev-panel {
  width: 100%; max-width: 960px; height: 85vh;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  display: flex; flex-direction: column; overflow: hidden;
  transition: transform 0.25s var(--spring);
}
.prev-hd {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 2px solid var(--color-border);
  font-size: 14px; font-weight: 700; font-family: var(--font-display);
}
.prev-close {
  width: 36px; height: 36px; border: 2px solid var(--color-border);
  background: var(--color-surface-hover);
  border-radius: 50%; cursor: pointer; box-shadow: none;
  display: flex; align-items: center; justify-content: center;
  color: var(--color-text);
  font-size: 18px; font-weight: 700;
}
.prev-close:hover { background: var(--color-danger-bg); border-color: var(--color-danger); color: var(--color-danger); box-shadow: none; }
.prev-bd { flex: 1; overflow: auto; }
.prev-loading { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-text-muted); font-size: 14px; font-weight: 600; }
.prev-iframe { width: 100%; height: 100%; border: none; }
.prev-html { padding: 24px; font-size: 15px; line-height: 1.8; color: var(--color-text); }
.prev-html :deep(h1), .prev-html :deep(h2), .prev-html :deep(h3) { margin: 16px 0 8px; }
.prev-html :deep(p) { margin-bottom: 8px; }
.prev-html :deep(table) { border-collapse: collapse; width: 100%; margin: 12px 0; }
.prev-html :deep(td), .prev-html :deep(th) { border: 1px solid var(--color-border); padding: 6px 12px; }
.prev-text {
  padding: 24px; margin: 0;
  font-size: 14px; line-height: 1.8; color: var(--color-text);
  white-space: pre-wrap; word-break: break-word;
}

@media (max-width: 640px) {
  .prev-overlay { padding: 12px; align-items: flex-end; }
  .prev-panel { height: 92vh; border-radius: var(--radius-xl) var(--radius-xl) 0 0; }
}
</style>
