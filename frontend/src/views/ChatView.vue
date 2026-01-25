<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useDevMode } from '@/composables/useDevMode'
import { marked } from 'marked'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const chat = useChatStore()
const { pacMode } = useDevMode()

const inputMessage = ref('')
const messagesContainer = ref(null)
const inputRef = ref(null)
const showSidebar = ref(true)

// Conversation management state
const searchQuery = ref('')
const editingConvId = ref(null)
const editingTitle = ref('')
const titleInputRef = ref(null)
const contextMenu = ref({ visible: false, x: 0, y: 0, conv: null })

// Native agents (all alchemical agents now have PAC versions)
const nativeAgents = [
  { id: 'AZOTH', name: 'Azoth', color: '#FFD700', symbol: '∴', isNative: true, hasPac: true },
  { id: 'ELYSIAN', name: 'Elysian', color: '#E8B4FF', symbol: '∴', isNative: true, hasPac: true },
  { id: 'VAJRA', name: 'Vajra', color: '#4FC3F7', symbol: '∴', isNative: true, hasPac: true },
  { id: 'KETHER', name: 'Kether', color: '#FFFFFF', symbol: '∴', isNative: true, hasPac: true },
  { id: 'CLAUDE', name: 'Claude', color: '#CC785C', symbol: 'C', isNative: true, hasPac: false },
]

// PAC agents (Perfected Stones - only visible in PAC mode)
const pacAgents = computed(() => {
  if (!pacMode.value) return []
  return nativeAgents
    .filter(a => a.hasPac)
    .map(a => ({
      ...a,
      id: a.id + '-PAC',
      name: a.name + '-Ω',
      isPac: true,
    }))
})

// Custom agents (loaded from API)
const customAgents = ref([])

// Combined agents list
const allAgents = computed(() => {
  const custom = customAgents.value.map(a => ({
    id: a.id,
    name: a.name,
    color: a.color,
    symbol: a.symbol,
    isNative: false,
    isPac: false,
  }))
  // PAC agents come first in PAC mode
  return [...pacAgents.value, ...nativeAgents.map(a => ({ ...a, isPac: false })), ...custom]
})

const selectedAgent = ref('AZOTH')

// Check if currently using a PAC agent
const isUsingPacAgent = computed(() => {
  return selectedAgent.value.endsWith('-PAC')
})

// Get the actual agent ID for API calls (strip -PAC suffix)
const actualAgentId = computed(() => {
  return selectedAgent.value.replace('-PAC', '')
})

// Load custom agents
async function fetchCustomAgents() {
  try {
    const response = await api.get('/api/v1/prompts/custom')
    customAgents.value = response.data?.agents || []
  } catch (e) {
    // Ignore errors (user might not be logged in)
    customAgents.value = []
  }
}

// Load conversation if ID in route
onMounted(async () => {
  await chat.fetchConversations()
  await fetchCustomAgents()

  if (route.params.id) {
    await chat.loadConversation(route.params.id)
  }

  inputRef.value?.focus()
})

// Watch for route changes
watch(() => route.params.id, async (newId) => {
  if (newId) {
    await chat.loadConversation(newId)
  } else {
    chat.createConversation()
  }
})

// Auto-scroll on new messages
watch(() => chat.messages.length, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})

async function handleSubmit() {
  const message = inputMessage.value.trim()
  if (!message || chat.isStreaming) return

  inputMessage.value = ''
  // Use actualAgentId and pass isPac flag for PAC prompt loading
  await chat.sendMessage(message, actualAgentId.value, undefined, isUsingPacAgent.value)
}

function newConversation() {
  chat.createConversation()
  router.push('/chat')
}

function selectConversation(conv) {
  router.push(`/chat/${conv.id}`)
  // Auto-close sidebar on mobile
  if (window.innerWidth < 768) {
    showSidebar.value = false
  }
}

// Filtered conversations (search)
const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) return chat.sortedConversations
  const q = searchQuery.value.toLowerCase()
  return chat.sortedConversations.filter(c =>
    c.title?.toLowerCase().includes(q)
  )
})

// Inline title editing
function startEdit(conv) {
  editingConvId.value = conv.id
  editingTitle.value = conv.title || ''
  nextTick(() => titleInputRef.value?.focus())
}

async function saveTitle() {
  if (editingConvId.value && editingTitle.value.trim()) {
    await chat.updateConversation(editingConvId.value, { title: editingTitle.value.trim() })
  }
  editingConvId.value = null
}

function cancelEdit() {
  editingConvId.value = null
}

// Context menu
function showContextMenu(event, conv) {
  event.preventDefault()
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    conv
  }
}

function hideContextMenu() {
  contextMenu.value.visible = false
}

async function handleContextAction(action) {
  const conv = contextMenu.value.conv
  if (!conv) return

  switch (action) {
    case 'rename':
      startEdit(conv)
      break
    case 'favorite':
      await chat.toggleFavorite(conv.id)
      break
    case 'archive':
      await chat.archiveConversation(conv.id)
      break
    case 'export':
      showExportModal.value = true
      exportConvId.value = conv.id
      break
    case 'delete':
      if (confirm('Delete this conversation?')) {
        await chat.deleteConversation(conv.id)
        if (chat.currentConversation?.id === conv.id) {
          router.push('/chat')
        }
      }
      break
  }
  hideContextMenu()
}

// Export modal
const showExportModal = ref(false)
const exportConvId = ref(null)

async function handleExport(format) {
  if (exportConvId.value) {
    await chat.exportConversation(exportConvId.value, format)
  }
  showExportModal.value = false
  exportConvId.value = null
}

function renderMarkdown(content) {
  return marked(content, { breaks: true })
}
</script>

<template>
  <div class="flex h-[calc(100vh-4rem)] relative">
    <!-- Mobile Sidebar Backdrop -->
    <div
      v-if="showSidebar"
      @click="showSidebar = false"
      class="md:hidden fixed inset-0 bg-black/50 z-20"
    ></div>

    <!-- Sidebar -->
    <aside
      class="fixed md:relative inset-y-0 left-0 z-30 w-72 bg-apex-dark border-r border-apex-border flex flex-col transform transition-transform duration-300 md:translate-x-0"
      :class="showSidebar ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
      :style="{ top: '4rem', height: 'calc(100vh - 4rem)' }"
    >
      <!-- Mobile Close Button -->
      <button
        @click="showSidebar = false"
        class="md:hidden absolute top-4 right-4 p-1 text-gray-400 hover:text-white z-10"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
      <!-- New Chat Button -->
      <div class="p-4 pb-2">
        <button
          @click="newConversation"
          class="btn-primary w-full flex items-center justify-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
          </svg>
          New Chat
        </button>
      </div>

      <!-- Search -->
      <div class="px-4 pb-2">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search conversations..."
          class="input text-sm py-2"
        />
      </div>

      <!-- Conversations List -->
      <div class="flex-1 overflow-y-auto px-2">
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          @click="selectConversation(conv)"
          @contextmenu="showContextMenu($event, conv)"
          class="group px-3 py-2 rounded-lg cursor-pointer transition-colors mb-1"
          :class="chat.currentConversation?.id === conv.id
            ? 'bg-gold/20 text-gold'
            : 'hover:bg-white/5 text-gray-300'"
        >
          <div class="flex items-center justify-between gap-2">
            <!-- Inline Title Edit -->
            <template v-if="editingConvId === conv.id">
              <input
                ref="titleInputRef"
                v-model="editingTitle"
                @keyup.enter="saveTitle"
                @keyup.escape="cancelEdit"
                @blur="saveTitle"
                @click.stop
                class="input text-sm py-1 flex-1"
              />
            </template>
            <template v-else>
              <span
                @dblclick.stop="startEdit(conv)"
                class="truncate text-sm flex-1"
                title="Double-click to rename"
              >
                {{ conv.title || 'New Conversation' }}
              </span>
            </template>

            <!-- Favorite Star (clickable) -->
            <button
              @click.stop="chat.toggleFavorite(conv.id)"
              class="text-xs transition-colors shrink-0"
              :class="conv.favorite
                ? 'text-gold'
                : 'text-gray-600 hover:text-gold/50 opacity-0 group-hover:opacity-100'"
              title="Toggle favorite"
            >
              {{ conv.favorite ? '★' : '☆' }}
            </button>
          </div>
          <div class="text-xs text-gray-500 mt-1">
            {{ new Date(conv.updated_at).toLocaleDateString() }}
          </div>
        </div>

        <div v-if="filteredConversations.length === 0 && searchQuery" class="text-center text-gray-500 text-sm py-8">
          No matches found
        </div>
        <div v-else-if="chat.conversations.length === 0" class="text-center text-gray-500 text-sm py-8">
          No conversations yet
        </div>
      </div>

      <!-- Agent Selector -->
      <div class="p-4 border-t border-apex-border" :class="{ 'border-purple-500/30': pacMode }">
        <label class="block text-xs mb-2" :class="pacMode ? 'text-purple-300/60' : 'text-gray-500'">
          {{ pacMode ? 'Invoke Agent' : 'Active Agent' }}
        </label>

        <!-- PAC Agents (shown first if in PAC mode) -->
        <div v-if="pacAgents.length > 0" class="mb-3">
          <div class="text-xs text-purple-300/40 mb-1">Perfected Stones</div>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="agent in pacAgents"
              :key="agent.id"
              @click="selectedAgent = agent.id"
              class="p-2 rounded text-center transition-all text-xs min-w-[3rem] agent-halo"
              :style="{
                backgroundColor: selectedAgent === agent.id ? agent.color + '33' : 'rgba(26, 10, 46, 0.6)',
                color: selectedAgent === agent.id ? agent.color : agent.color + '80',
                boxShadow: selectedAgent === agent.id
                  ? `inset 0 0 0 1px ${agent.color}, 0 0 15px ${agent.color}40`
                  : `inset 0 0 0 1px ${agent.color}30`,
              }"
              :title="agent.name + ' (Perfected Stone)'"
            >
              {{ agent.symbol }}Ω
            </button>
          </div>
        </div>

        <!-- Regular Agents -->
        <div class="flex flex-wrap gap-1">
          <button
            v-for="agent in allAgents.filter(a => !a.isPac)"
            :key="agent.id"
            @click="selectedAgent = agent.id"
            class="p-2 rounded text-center transition-all text-xs min-w-[2.5rem]"
            :style="{
              backgroundColor: selectedAgent === agent.id ? agent.color + '33' : 'transparent',
              color: selectedAgent === agent.id ? agent.color : '#9ca3af',
              boxShadow: selectedAgent === agent.id ? `inset 0 0 0 1px ${agent.color}` : 'none',
            }"
            :title="agent.name + (agent.isNative ? '' : ' (Custom)')"
          >
            {{ agent.symbol || '+' }}{{ agent.name.charAt(0) }}
          </button>
        </div>
        <div v-if="customAgents.length > 0" class="mt-2 text-xs text-gray-500">
          + {{ customAgents.length }} custom
        </div>
      </div>
    </aside>

    <!-- Main Chat Area -->
    <main
      class="flex-1 flex flex-col transition-all duration-500"
      :class="isUsingPacAgent ? 'pac-chat-area' : 'bg-apex-darker'"
      :style="isUsingPacAgent ? {
        background: 'radial-gradient(ellipse at center, rgba(26, 10, 46, 0.95) 0%, rgba(10, 6, 18, 0.98) 100%)'
      } : {}"
    >
      <!-- Toggle Sidebar (mobile) -->
      <button
        v-if="!showSidebar"
        @click="showSidebar = true"
        class="md:hidden fixed top-20 left-4 z-40 p-2 bg-apex-card border border-apex-border rounded-lg shadow-lg"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
        </svg>
      </button>

      <!-- Messages -->
      <div
        ref="messagesContainer"
        class="flex-1 overflow-y-auto px-4 py-6"
      >
        <div class="max-w-3xl mx-auto space-y-6">
          <!-- Welcome message if no messages -->
          <div v-if="chat.messages.length === 0" class="text-center py-20">
            <div class="text-6xl font-serif font-bold text-gold mb-4">Au</div>
            <h2 class="text-2xl font-bold mb-2">Welcome to ApexAurum Cloud</h2>
            <p class="text-gray-400 mb-8">140 Tools. Five Minds. One Village.</p>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-xl mx-auto text-sm">
              <button
                @click="inputMessage = 'What can you help me with?'"
                class="btn-secondary text-left"
              >
                What can you do?
              </button>
              <button
                @click="inputMessage = 'Tell me about the Village Protocol'"
                class="btn-secondary text-left"
              >
                Village Protocol
              </button>
              <button
                @click="inputMessage = 'Generate some music for me'"
                class="btn-secondary text-left"
              >
                Generate Music
              </button>
              <button
                @click="inputMessage = 'Spawn a research agent'"
                class="btn-secondary text-left"
              >
                Spawn Agent
              </button>
            </div>
          </div>

          <!-- Message list -->
          <div
            v-for="message in chat.messages"
            :key="message.id"
            class="flex gap-4"
            :class="message.role === 'user' ? 'justify-end' : ''"
          >
            <!-- Avatar -->
            <div
              v-if="message.role !== 'user'"
              class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all"
              :class="message.role === 'system'
                ? 'bg-red-500/20'
                : isUsingPacAgent
                  ? 'agent-halo'
                  : 'bg-gold/20'"
              :style="isUsingPacAgent && message.role === 'assistant' ? {
                backgroundColor: 'rgba(255, 215, 0, 0.15)',
                boxShadow: '0 0 20px rgba(255, 215, 0, 0.3)'
              } : {}"
            >
              <span v-if="message.role === 'assistant'" class="text-gold font-serif font-bold text-sm">
                {{ isUsingPacAgent ? '∴' : 'Au' }}
              </span>
              <span v-else class="text-red-400 text-sm">!</span>
            </div>

            <!-- Message content -->
            <div
              class="max-w-[80%] rounded-2xl px-4 py-3 transition-all"
              :class="{
                'bg-gold text-apex-dark': message.role === 'user',
                'bg-apex-card': message.role === 'assistant' && !isUsingPacAgent,
                'pac-message': message.role === 'assistant' && isUsingPacAgent,
                'bg-red-500/10 border border-red-500/30': message.role === 'system'
              }"
            >
              <div
                v-if="message.role === 'assistant'"
                class="prose prose-sm max-w-none"
                :class="isUsingPacAgent ? 'prose-purple' : 'prose-invert'"
                :style="isUsingPacAgent ? { color: '#E8B4FF' } : {}"
                v-html="renderMarkdown(message.content)"
              />
              <div v-else>{{ message.content }}</div>
            </div>

            <!-- User avatar -->
            <div
              v-if="message.role === 'user'"
              class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
              :class="isUsingPacAgent
                ? 'bg-gradient-to-br from-purple-400 to-purple-600'
                : 'bg-gradient-to-br from-gold to-gold-dim'"
            >
              <span class="text-apex-dark font-bold text-sm">Y</span>
            </div>
          </div>

          <!-- Streaming indicator -->
          <div v-if="chat.isStreaming" class="flex gap-4">
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
              :class="isUsingPacAgent ? 'agent-halo' : 'bg-gold/20'"
              :style="isUsingPacAgent ? {
                backgroundColor: 'rgba(255, 215, 0, 0.15)',
                boxShadow: '0 0 20px rgba(255, 215, 0, 0.3)'
              } : {}"
            >
              <span class="text-gold font-serif font-bold text-sm">{{ isUsingPacAgent ? '∴' : 'Au' }}</span>
            </div>
            <div :class="isUsingPacAgent ? 'pac-message' : 'bg-apex-card'" class="rounded-2xl px-4 py-3">
              <div class="flex items-center gap-2" :class="isUsingPacAgent ? 'text-purple-300' : 'text-gray-400'">
                <div class="flex gap-1">
                  <span class="w-2 h-2 rounded-full animate-bounce" :class="isUsingPacAgent ? 'bg-purple-400' : 'bg-gold'" style="animation-delay: 0ms"></span>
                  <span class="w-2 h-2 rounded-full animate-bounce" :class="isUsingPacAgent ? 'bg-purple-400' : 'bg-gold'" style="animation-delay: 150ms"></span>
                  <span class="w-2 h-2 rounded-full animate-bounce" :class="isUsingPacAgent ? 'bg-purple-400' : 'bg-gold'" style="animation-delay: 300ms"></span>
                </div>
                <span class="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div
        class="border-t p-4 transition-all"
        :class="isUsingPacAgent ? 'border-purple-500/30' : 'border-apex-border'"
      >
        <form @submit.prevent="handleSubmit" class="max-w-3xl mx-auto">
          <div class="flex gap-3">
            <input
              ref="inputRef"
              v-model="inputMessage"
              type="text"
              :placeholder="isUsingPacAgent ? 'Speak to the Stone...' : 'Message ApexAurum...'"
              class="input flex-1"
              :class="isUsingPacAgent ? 'pac-input' : ''"
              :style="isUsingPacAgent ? {
                background: 'rgba(26, 10, 46, 0.8)',
                borderColor: 'rgba(255, 215, 0, 0.2)',
              } : {}"
              :disabled="chat.isStreaming"
            />
            <button
              type="submit"
              class="px-6 rounded-lg font-medium transition-all"
              :class="isUsingPacAgent ? '' : 'btn-primary'"
              :style="isUsingPacAgent ? {
                background: 'rgba(255, 215, 0, 0.15)',
                border: '1px solid rgba(255, 215, 0, 0.4)',
                color: '#FFD700',
                boxShadow: '0 0 20px rgba(255, 215, 0, 0.2)'
              } : {}"
              :disabled="!inputMessage.trim() || chat.isStreaming"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </div>
          <p class="text-xs mt-2 text-center" :class="isUsingPacAgent ? 'text-purple-300/60' : 'text-gray-500'">
            <template v-if="isUsingPacAgent">
              <span class="text-gold">∴ {{ actualAgentId }}-Ω ∴</span> · Perfected Stone Active
            </template>
            <template v-else>
              Agent: <span class="text-gold">{{ selectedAgent }}</span> |
              Press Enter to send
            </template>
          </p>
        </form>
      </div>
    </main>

    <!-- Context Menu -->
    <Teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="fixed bg-apex-card border border-apex-border rounded-lg shadow-xl py-1 z-50 min-w-[160px]"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      >
        <button
          @click="handleContextAction('rename')"
          class="w-full px-4 py-2 text-left text-sm hover:bg-white/5 flex items-center gap-2"
        >
          <span class="text-gray-400">✏️</span> Rename
        </button>
        <button
          @click="handleContextAction('favorite')"
          class="w-full px-4 py-2 text-left text-sm hover:bg-white/5 flex items-center gap-2"
        >
          <span class="text-gray-400">{{ contextMenu.conv?.favorite ? '☆' : '★' }}</span>
          {{ contextMenu.conv?.favorite ? 'Unfavorite' : 'Favorite' }}
        </button>
        <button
          @click="handleContextAction('export')"
          class="w-full px-4 py-2 text-left text-sm hover:bg-white/5 flex items-center gap-2"
        >
          <span class="text-gray-400">📤</span> Export
        </button>
        <button
          @click="handleContextAction('archive')"
          class="w-full px-4 py-2 text-left text-sm hover:bg-white/5 flex items-center gap-2"
        >
          <span class="text-gray-400">📦</span> Archive
        </button>
        <hr class="border-apex-border my-1" />
        <button
          @click="handleContextAction('delete')"
          class="w-full px-4 py-2 text-left text-sm hover:bg-red-500/10 text-red-400 flex items-center gap-2"
        >
          <span>🗑️</span> Delete
        </button>
      </div>
      <!-- Click outside to close -->
      <div
        v-if="contextMenu.visible"
        @click="hideContextMenu"
        class="fixed inset-0 z-40"
      ></div>
    </Teleport>

    <!-- Export Modal -->
    <Teleport to="body">
      <div
        v-if="showExportModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showExportModal = false"
      >
        <div class="card w-80">
          <h3 class="text-lg font-bold mb-4">Export Conversation</h3>
          <div class="space-y-2">
            <button
              @click="handleExport('json')"
              class="btn-secondary w-full text-left flex items-center gap-3"
            >
              <span class="text-lg">📄</span>
              <div>
                <div class="font-medium">JSON</div>
                <div class="text-xs text-gray-500">Full data, re-importable</div>
              </div>
            </button>
            <button
              @click="handleExport('markdown')"
              class="btn-secondary w-full text-left flex items-center gap-3"
            >
              <span class="text-lg">📝</span>
              <div>
                <div class="font-medium">Markdown</div>
                <div class="text-xs text-gray-500">Readable, shareable</div>
              </div>
            </button>
            <button
              @click="handleExport('txt')"
              class="btn-secondary w-full text-left flex items-center gap-3"
            >
              <span class="text-lg">📃</span>
              <div>
                <div class="font-medium">Plain Text</div>
                <div class="text-xs text-gray-500">Simple format</div>
              </div>
            </button>
          </div>
          <button
            @click="showExportModal = false"
            class="btn-ghost w-full mt-4"
          >
            Cancel
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* Bounce animation for typing indicator */
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
</style>
