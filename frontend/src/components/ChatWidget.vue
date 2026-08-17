<template>
  <div class="chat-widget" v-if="isDesktop">
    <!-- Floating Button -->
    <button class="chat-fab" @click="open = !open" :class="{ active: open }">
      <svg v-if="!open" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <!-- Chat Panel -->
    <div v-if="open" class="chat-panel">
      <div class="chat-panel-header">
        <span class="chat-panel-title">서비스 상담</span>
        <span class="chat-panel-sub">무엇이든 물어보세요</span>
      </div>
      <div class="chat-messages" ref="messagesEl">
        <div v-for="(msg, i) in messages" :key="i" class="chat-msg" :class="msg.role">
          <div class="msg-bubble">{{ msg.content }}</div>
        </div>
        <div v-if="loading" class="chat-msg bot">
          <div class="msg-bubble typing">
            <span class="dot-anim"></span>
            <span class="dot-anim"></span>
            <span class="dot-anim"></span>
          </div>
        </div>
      </div>
      <form class="chat-input-form" @submit.prevent="sendMessage">
        <input
          v-model="input"
          class="chat-input"
          placeholder="메시지를 입력하세요..."
          :disabled="loading"
          autocomplete="off"
        />
        <button type="submit" class="chat-send" :disabled="!input.trim() || loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const open = ref(false)
const input = ref('')
const loading = ref(false)
const messages = ref([
  { role: 'bot', content: '안녕하세요! 서비스에 대해 궁금한 점이 있으시면 물어보세요.' }
])
const messagesEl = ref(null)
const history = ref([])
const isDesktop = ref(window.innerWidth >= 1024)

function onResize() { isDesktop.value = window.innerWidth >= 1024 }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

function scrollBottom() {
  nextTick(() => {
    if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  })
}

async function sendMessage() {
  if (!input.value.trim() || loading.value) return
  const text = input.value.trim()
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  history.value.push({ role: 'user', content: text })
  loading.value = true
  scrollBottom()

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: history.value.slice(-10) })
    })
    const data = await res.json()
    const reply = data.reply || '다시 말씀해 주시겠어요?'
    history.value.push({ role: 'assistant', content: reply })
    messages.value.push({ role: 'bot', content: reply })
  } catch {
    messages.value.push({ role: 'bot', content: '일시적인 오류가 발생했습니다. 다시 시도해주세요.' })
  } finally {
    loading.value = false
    scrollBottom()
  }
}
</script>

<style scoped>
.chat-widget {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 999;
}

.chat-fab {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--accent-color, #6366f1);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
  transition: transform 0.15s, box-shadow 0.15s;
}

.chat-fab:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 28px rgba(99, 102, 241, 0.5);
}

.chat-fab.active {
  background: var(--bg-tertiary, #333);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.chat-panel {
  position: absolute;
  bottom: 64px;
  right: 0;
  width: 360px;
  height: 480px;
  background: var(--bg-secondary, #fff);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-panel-header {
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-panel-title {
  display: block;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
}

.chat-panel-sub {
  display: block;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-msg {
  display: flex;
}

.chat-msg.bot {
  justify-content: flex-start;
}

.chat-msg.user {
  justify-content: flex-end;
}

.msg-bubble {
  max-width: 80%;
  padding: 10px 14px;
  font-size: 0.82rem;
  line-height: 1.5;
  border-radius: 12px;
  word-break: break-word;
}

.chat-msg.bot .msg-bubble {
  background: var(--bg-surface, #f4f4f5);
  color: var(--text-primary);
  border-radius: 12px 12px 12px 4px;
}

.chat-msg.user .msg-bubble {
  background: var(--accent-color, #6366f1);
  color: #fff;
  border-radius: 12px 12px 4px 12px;
}

.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 18px;
}

.dot-anim {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: dotBounce 1.2s ease-in-out infinite;
}

.dot-anim:nth-child(2) { animation-delay: 0.15s; }
.dot-anim:nth-child(3) { animation-delay: 0.3s; }

@keyframes dotBounce {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-4px); }
}

.chat-input-form {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  background: var(--bg-primary, #fafafa);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 8px 14px;
  font-size: 0.82rem;
  color: var(--text-primary);
  outline: none;
  font-family: inherit;
}

.chat-input:focus {
  border-color: var(--accent-color, #6366f1);
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.chat-send {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--accent-color, #6366f1);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.15s;
}

.chat-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
