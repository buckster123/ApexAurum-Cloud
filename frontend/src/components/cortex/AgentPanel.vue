<script setup>
/**
 * Agent Panel - AI Code Assistant for Cortex Diver
 *
 * Provides code-aware chat with the ability to:
 * - See and discuss selected code
 * - Propose and apply edits
 * - Stream responses in real-time
 */

import { ref, computed, watch, nextTick } from 'vue'
import { useSound } from '@/composables/useSound'

const props = defineProps({
  selection: {
    type: Object,
    default: null,
    // { text, range, filename, language }
  },
  activeFile: {
    type: Object,
    default: null,
    // { id, name, fileType }
  },
})

const emit = defineEmits(['apply-code', 'close'])

const { playTone } = useSound()

// Chat state
const messages = ref([])
const inputMessage = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const messagesContainer = ref(null)

// Code suggestion state
const pendingCodeSuggestion = ref(null)

// Sounds
const agentSounds = {
  send: () => playTone(523, 0.08, 'sine', 0.15),
  receive: () => playTone(659, 0.1, 'sine', 0.12),
  apply: () => playTone(880, 0.15, 'sine', 0.2),
}

// Build context message with code selection
function buildContextMessage(userMessage) {
  let context = ''

  if (props.selection?.text) {
    context += `I'm looking at this code from \`${props.activeFile?.name || 'file'}\`:\n\n`
    context += '```' + (props.selection.language || '') + '\n'
    context += props.selection.text
    context += '\n```\n\n'
  }

  if (props.activeFile) {
    context += `File: ${props.activeFile.name}\n\n`
  }

  return context + userMessage
}

// Extract code blocks from response
function extractCodeBlocks(text) {
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g
  const blocks = []
  let match

  while ((match = codeBlockRegex.exec(text)) !== null) {
    blocks.push({
      language: match[1] || 'plaintext',
      code: match[2].trim(),
      fullMatch: match[0],
    })
  }

  return blocks
}

// Send message to agent
async function sendMessage() {
  if (!inputMessage.value.trim() || isStreaming.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // Add user message
  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: userMessage,
    codeContext: props.selection?.text || null,
  })

  agentSounds.send()
  scrollToBottom()

  // Build full context message
  const contextMessage = buildContextMessage(userMessage)

  // Start streaming
  isStreaming.value = true
  streamingContent.value = ''

  // Add placeholder for assistant
  const assistantMsgId = Date.now().toString() + '-assistant'
  messages.value.push({
    id: assistantMsgId,
    role: 'assistant',
    content: '',
  })

  try {
    const apiUrl = import.meta.env.VITE_API_URL || ''
    const token = localStorage.getItem('accessToken')

    const response = await fetch(`${apiUrl}/api/v1/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: JSON.stringify({
        message: contextMessage,
        agent: 'CLAUDE',  // Use Claude for code assistance
        stream: true,
        max_tokens: 4096,
        // Don't save to conversation history - ephemeral code chat
        save_conversation: false,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    // Read SSE stream
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue

        try {
          const data = JSON.parse(line.slice(6))

          if (data.type === 'token' && data.content) {
            streamingContent.value += data.content
            const msg = messages.value.find(m => m.id === assistantMsgId)
            if (msg) msg.content += data.content
            scrollToBottom()
          } else if (data.type === 'error') {
            throw new Error(data.message || 'Stream error')
          }
        } catch (parseError) {
          console.warn('Failed to parse SSE:', parseError)
        }
      }
    }

    // Check for code blocks in response
    const msg = messages.value.find(m => m.id === assistantMsgId)
    if (msg) {
      const codeBlocks = extractCodeBlocks(msg.content)
      if (codeBlocks.length > 0) {
        msg.codeBlocks = codeBlocks
      }
    }

    agentSounds.receive()

  } catch (e) {
    console.error('Agent chat error:', e)
    const msg = messages.value.find(m => m.id === assistantMsgId)
    if (msg) {
      msg.role = 'error'
      msg.content = `Error: ${e.message}`
    }
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
  }
}

// Apply code suggestion to editor
function applyCode(code) {
  agentSounds.apply()
  emit('apply-code', code)
}

// Scroll to bottom of messages
async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Handle keyboard shortcuts
function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// Clear chat
function clearChat() {
  messages.value = []
  pendingCodeSuggestion.value = null
}

// Watch for selection changes to add context indicator
watch(() => props.selection, (newSelection) => {
  if (newSelection?.text && newSelection.action === 'ask-agent') {
    // Focus input when triggered via Ctrl+Shift+A
    nextTick(() => {
      document.querySelector('.agent-input')?.focus()
    })
  }
})
</script>

<template>
  <div class="flex flex-col h-full bg-apex-darker">
    <!-- Header -->
    <div class="flex items-center justify-between px-3 py-2 border-b border-apex-border">
      <div class="flex items-center gap-2">
        <span class="text-amber-400">🧠</span>
        <span class="text-xs text-amber-400 uppercase tracking-wider font-medium">Agent</span>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="clearChat"
          class="text-gray-500 hover:text-gray-300 text-xs"
          title="Clear chat"
        >
          Clear
        </button>
        <button
          @click="emit('close')"
          class="text-gray-500 hover:text-gray-300"
          title="Close panel"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Code context indicator -->
    <div
      v-if="selection?.text"
      class="px-3 py-2 bg-amber-900/20 border-b border-amber-600/20"
    >
      <div class="flex items-center justify-between">
        <span class="text-xs text-amber-400">
          {{ selection.text.split('\n').length }} lines selected
        </span>
        <span class="text-xs text-gray-500">
          {{ activeFile?.name || 'Unknown file' }}
        </span>
      </div>
      <pre class="text-xs text-gray-400 mt-1 max-h-20 overflow-hidden font-mono">{{ selection.text.slice(0, 200) }}{{ selection.text.length > 200 ? '...' : '' }}</pre>
    </div>

    <!-- Messages -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-3 space-y-3"
    >
      <!-- Empty state -->
      <div
        v-if="messages.length === 0"
        class="flex flex-col items-center justify-center h-full text-gray-500"
      >
        <div class="text-3xl mb-2 opacity-30">🧠</div>
        <p class="text-sm">Ask about your code</p>
        <p class="text-xs mt-1 text-gray-600">
          Select code + <kbd class="px-1 py-0.5 bg-apex-dark rounded text-xs">Ctrl+Shift+A</kbd>
        </p>
      </div>

      <!-- Message list -->
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="text-sm"
      >
        <!-- User message -->
        <div
          v-if="msg.role === 'user'"
          class="flex justify-end"
        >
          <div class="max-w-[85%] bg-amber-900/30 rounded-lg px-3 py-2">
            <p class="text-gray-200 whitespace-pre-wrap">{{ msg.content }}</p>
            <p
              v-if="msg.codeContext"
              class="text-xs text-amber-500/50 mt-1"
            >
              + code context
            </p>
          </div>
        </div>

        <!-- Assistant message -->
        <div
          v-else-if="msg.role === 'assistant'"
          class="flex justify-start"
        >
          <div class="max-w-[95%]">
            <div class="bg-apex-dark rounded-lg px-3 py-2 prose prose-invert prose-sm max-w-none">
              <div class="text-gray-300 whitespace-pre-wrap" v-html="formatMessage(msg.content)"></div>
            </div>

            <!-- Code suggestion actions -->
            <div
              v-if="msg.codeBlocks?.length > 0"
              class="mt-2 space-y-2"
            >
              <div
                v-for="(block, idx) in msg.codeBlocks"
                :key="idx"
                class="bg-apex-dark border border-amber-600/20 rounded-lg overflow-hidden"
              >
                <div class="flex items-center justify-between px-2 py-1 bg-amber-900/20 border-b border-amber-600/20">
                  <span class="text-xs text-amber-400">{{ block.language }}</span>
                  <button
                    @click="applyCode(block.code)"
                    class="text-xs text-amber-300 hover:text-amber-100 px-2 py-0.5 bg-amber-700/30 rounded hover:bg-amber-600/40 transition-colors"
                  >
                    Apply to Editor
                  </button>
                </div>
                <pre class="text-xs text-gray-300 p-2 overflow-x-auto max-h-40 font-mono">{{ block.code }}</pre>
              </div>
            </div>
          </div>
        </div>

        <!-- Error message -->
        <div
          v-else-if="msg.role === 'error'"
          class="text-red-400 text-xs bg-red-900/20 rounded-lg px-3 py-2"
        >
          {{ msg.content }}
        </div>
      </div>

      <!-- Streaming indicator -->
      <div
        v-if="isStreaming"
        class="flex items-center gap-2 text-amber-400 text-xs"
      >
        <div class="animate-pulse">●</div>
        <span>Thinking...</span>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-apex-border p-3">
      <div class="flex gap-2">
        <textarea
          v-model="inputMessage"
          @keydown="handleKeydown"
          placeholder="Ask about your code..."
          class="agent-input flex-1 bg-apex-dark border border-apex-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 resize-none focus:border-amber-600/50 focus:outline-none"
          rows="2"
          :disabled="isStreaming"
        ></textarea>
        <button
          @click="sendMessage"
          :disabled="isStreaming || !inputMessage.trim()"
          class="px-3 py-2 bg-amber-600 hover:bg-amber-500 disabled:bg-gray-700 disabled:text-gray-500 text-black font-medium rounded-lg transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      <p class="text-xs text-gray-600 mt-1">
        Enter to send · Shift+Enter for newline
      </p>
    </div>
  </div>
</template>

<script>
// Helper to format message content (basic markdown-like)
function formatMessage(content) {
  if (!content) return ''

  // Escape HTML first
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // Inline code (but not code blocks)
  html = html.replace(/`([^`\n]+)`/g, '<code class="bg-apex-darker px-1 rounded text-amber-300">$1</code>')

  // Code blocks are handled separately, so we can leave them as-is for the pre display

  return html
}
</script>

<style scoped>
.prose code {
  @apply bg-apex-darker px-1 rounded text-amber-300;
}
</style>
