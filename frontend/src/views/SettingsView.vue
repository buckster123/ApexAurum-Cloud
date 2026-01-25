<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useDevMode } from '@/composables/useDevMode'
import api from '@/services/api'

const auth = useAuthStore()
const { devMode, pacMode, handleTap, tapCount, alchemyLayer, layerName } = useDevMode()

// Active tab for dev mode
const activeTab = ref('profile')
const devTabs = ['profile', 'agents', 'import', 'advanced', 'api']

// Import state
const importing = ref(false)
const importResult = ref({ conversations: null, memory: null })

// Profile
const displayName = ref('')
const loading = ref(false)
const saved = ref(false)

// Preferences
const preferences = ref({
  default_model: 'claude-3-haiku-20240307',
  cache_strategy: 'balanced',
  context_strategy: 'adaptive',
  theme: 'dark',
  default_agent: 'AZOTH',
  streaming: true,
  max_tokens: 4096,
  temperature: 0.7,
})

// Usage stats
const usage = ref(null)

// Native agents (from API)
const nativeAgents = ref([])
const loadingAgents = ref(false)

// Custom agents
const customAgents = ref([])

// Agent editor modal
const showAgentEditor = ref(false)
const editingAgent = ref(null)
const viewingPrompt = ref(null)
const showPromptViewer = ref(false)

// PAC Mode - Perfected Stones
const showCodexViewer = ref(false)
const viewingCodex = ref(null)

// Computed: Agents that have PAC versions
const pacAgents = computed(() => nativeAgents.value.filter(a => a.has_pac))

const models = [
  { id: 'claude-3-haiku-20240307', name: 'Haiku (Fast)' },
  { id: 'claude-sonnet-4-20250514', name: 'Sonnet 4' },
  { id: 'claude-opus-4-20250514', name: 'Opus 4' },
]

const cacheStrategies = [
  { id: 'disabled', name: 'Disabled' },
  { id: 'conservative', name: 'Conservative' },
  { id: 'balanced', name: 'Balanced' },
  { id: 'aggressive', name: 'Aggressive' },
]

const contextStrategies = [
  { id: 'disabled', name: 'Disabled' },
  { id: 'balanced', name: 'Balanced' },
  { id: 'adaptive', name: 'Adaptive' },
  { id: 'aggressive', name: 'Aggressive' },
  { id: 'rolling', name: 'Rolling' },
]

const agents = ['AZOTH', 'ELYSIAN', 'VAJRA', 'KETHER', 'CLAUDE']

// Computed
const tapProgress = computed(() => Math.min(tapCount.value / 7 * 100, 100))

onMounted(async () => {
  displayName.value = auth.user?.display_name || ''
  await fetchPreferences()
  await fetchUsage()

  if (devMode.value) {
    await fetchNativeAgents()
    await fetchCustomAgents()
  }
})

async function fetchPreferences() {
  try {
    const response = await api.get('/api/v1/user/preferences')
    preferences.value = { ...preferences.value, ...response.data }
  } catch (e) {
    console.error('Failed to fetch preferences:', e)
  }
}

async function fetchUsage() {
  try {
    const response = await api.get('/api/v1/user/usage')
    usage.value = response.data
  } catch (e) {
    console.error('Failed to fetch usage:', e)
  }
}

async function fetchNativeAgents() {
  loadingAgents.value = true
  try {
    const response = await api.get('/api/v1/prompts/native')
    nativeAgents.value = response.data?.agents || []
  } catch (e) {
    console.error('Failed to fetch native agents:', e)
  } finally {
    loadingAgents.value = false
  }
}

async function fetchCustomAgents() {
  try {
    const response = await api.get('/api/v1/prompts/custom')
    customAgents.value = response.data?.agents || []
  } catch (e) {
    console.error('Failed to fetch custom agents:', e)
  }
}

async function saveProfile() {
  loading.value = true
  saved.value = false
  try {
    await api.put('/api/v1/user/profile', {
      display_name: displayName.value
    })
    auth.user.display_name = displayName.value
    saved.value = true
    setTimeout(() => saved.value = false, 3000)
  } catch (e) {
    console.error('Failed to save profile:', e)
  } finally {
    loading.value = false
  }
}

async function savePreferences() {
  loading.value = true
  saved.value = false
  try {
    await api.put('/api/v1/user/preferences', preferences.value)
    saved.value = true
    setTimeout(() => saved.value = false, 3000)
  } catch (e) {
    console.error('Failed to save preferences:', e)
  } finally {
    loading.value = false
  }
}

async function viewNativePrompt(agentId) {
  try {
    const response = await api.get(`/api/v1/prompts/native/${agentId}`)
    viewingPrompt.value = response.data
    showPromptViewer.value = true
  } catch (e) {
    console.error('Failed to load prompt:', e)
  }
}

// View PAC Codex (The Perfected Stone's true form)
async function viewCodex(agentId) {
  try {
    const response = await api.get(`/api/v1/prompts/native/${agentId}?prompt_type=pac`)
    viewingCodex.value = response.data
    showCodexViewer.value = true
  } catch (e) {
    console.error('Failed to load codex:', e)
  }
}

async function copyToCustom(agent) {
  try {
    const response = await api.get(`/api/v1/prompts/native/${agent.id}`)
    editingAgent.value = {
      id: null, // Will generate new ID
      name: `${response.data.name} (Copy)`,
      symbol: response.data.symbol,
      color: response.data.color,
      prompt: response.data.prompt,
      type: response.data.type,
    }
    showAgentEditor.value = true
  } catch (e) {
    console.error('Failed to copy prompt:', e)
  }
}

function createNewAgent() {
  editingAgent.value = {
    id: null,
    name: 'New Agent',
    symbol: '+',
    color: '#888888',
    prompt: 'You are a helpful AI assistant.',
    type: 'prose',
  }
  showAgentEditor.value = true
}

function editCustomAgent(agent) {
  editingAgent.value = { ...agent }
  showAgentEditor.value = true
}

async function saveAgent() {
  try {
    await api.post('/api/v1/prompts/custom', editingAgent.value)
    await fetchCustomAgents()
    showAgentEditor.value = false
    editingAgent.value = null
  } catch (e) {
    console.error('Failed to save agent:', e)
  }
}

async function deleteCustomAgent(agentId) {
  if (!confirm('Delete this custom agent?')) return

  try {
    await api.delete(`/api/v1/prompts/custom/${agentId}`)
    await fetchCustomAgents()
  } catch (e) {
    console.error('Failed to delete agent:', e)
  }
}

function formatCost(cost) {
  return `$${cost.toFixed(4)}`
}

// Tab switching triggers data loading
async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'agents' && nativeAgents.value.length === 0) {
    await fetchNativeAgents()
    await fetchCustomAgents()
  }
}

// Import handlers
async function handleConversationsImport(event) {
  const file = event.target.files[0]
  if (!file) return

  importing.value = true
  importResult.value.conversations = null

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/api/v1/import/conversations', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    importResult.value.conversations = `Imported ${response.data.imported} conversations`
    if (response.data.skipped > 0) {
      importResult.value.conversations += ` (${response.data.skipped} skipped)`
    }
  } catch (e) {
    importResult.value.conversations = `Error: ${e.response?.data?.detail || e.message}`
  } finally {
    importing.value = false
    event.target.value = '' // Reset file input
  }
}

async function handleMemoryImport(event) {
  const file = event.target.files[0]
  if (!file) return

  importing.value = true
  importResult.value.memory = null

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/api/v1/import/memory', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    importResult.value.memory = `Imported ${response.data.imported} memory entries`
    if (response.data.skipped > 0) {
      importResult.value.memory += ` (${response.data.skipped} skipped)`
    }
  } catch (e) {
    importResult.value.memory = `Error: ${e.response?.data?.detail || e.message}`
  } finally {
    importing.value = false
    event.target.value = '' // Reset file input
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <!-- Header with Au logo (tap target) -->
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-3xl font-bold">Settings</h1>

      <div class="flex items-center gap-3">
        <!-- Layer Badges -->
        <span
          v-if="pacMode"
          class="pac-badge px-3 py-1 text-xs font-bold rounded"
        >
          THE ADEPT
        </span>
        <span
          v-else-if="devMode"
          class="px-2 py-1 text-xs font-bold bg-gold/20 text-gold rounded"
        >
          DEV
        </span>

        <!-- Au Logo - tap target for easter egg -->
        <button
          @click="handleTap"
          class="relative w-12 h-12 rounded-full bg-gradient-to-br from-gold to-gold-dim flex items-center justify-center font-serif font-bold text-xl text-apex-dark hover:scale-105 transition-transform"
          title="ApexAurum"
        >
          Au
          <!-- Tap progress indicator -->
          <svg
            v-if="tapCount > 0 && !devMode"
            class="absolute inset-0 w-12 h-12 -rotate-90"
          >
            <circle
              cx="24" cy="24" r="22"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-dasharray="138.2"
              :stroke-dashoffset="138.2 - (tapProgress / 100 * 138.2)"
              class="text-white/50"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Success message -->
    <div
      v-if="saved"
      class="mb-6 p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm"
    >
      Settings saved successfully!
    </div>

    <!-- Dev Mode: Tab Navigation (scrollable on mobile) -->
    <div v-if="devMode" class="flex gap-2 mb-6 border-b border-apex-border overflow-x-auto scrollbar-hide pb-px -mb-px">
      <button
        v-for="tab in devTabs"
        :key="tab"
        @click="switchTab(tab)"
        class="px-4 py-3 text-sm font-medium transition-colors capitalize whitespace-nowrap flex-shrink-0"
        :class="activeTab === tab
          ? 'text-gold border-b-2 border-gold'
          : 'text-gray-400 hover:text-white'"
      >
        {{ tab }}
      </button>
    </div>

    <!-- PROFILE TAB (shown in both modes) -->
    <template v-if="activeTab === 'profile' || !devMode">
      <!-- Profile Section -->
      <div class="card mb-6">
        <h2 class="text-xl font-bold mb-4">Profile</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-2">Email</label>
            <input
              type="email"
              :value="auth.user?.email"
              disabled
              class="input bg-apex-darker cursor-not-allowed"
            />
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-2">Display Name</label>
            <input
              v-model="displayName"
              type="text"
              class="input"
              placeholder="How should we call you?"
            />
          </div>

          <button
            @click="saveProfile"
            class="btn-primary"
            :disabled="loading"
          >
            {{ loading ? 'Saving...' : 'Save Profile' }}
          </button>
        </div>
      </div>

      <!-- Preferences Section (Standard Mode shows simplified) -->
      <div class="card mb-6">
        <h2 class="text-xl font-bold mb-4">Preferences</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-2">Default Agent</label>
            <select v-model="preferences.default_agent" class="input">
              <option v-for="agent in agents" :key="agent" :value="agent">
                {{ agent }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-2">Theme</label>
            <select v-model="preferences.theme" class="input">
              <option value="dark">Dark</option>
              <option value="light" disabled>Light (Coming Soon)</option>
            </select>
          </div>

          <div class="flex items-center gap-3">
            <input
              type="checkbox"
              id="streaming"
              v-model="preferences.streaming"
              class="w-4 h-4 rounded border-gray-600 text-gold focus:ring-gold"
            />
            <label for="streaming" class="text-sm text-gray-300">
              Enable streaming responses
            </label>
          </div>

          <button
            @click="savePreferences"
            class="btn-primary"
            :disabled="loading"
          >
            {{ loading ? 'Saving...' : 'Save Preferences' }}
          </button>
        </div>
      </div>

      <!-- Usage Statistics (Standard Mode) -->
      <div v-if="!devMode" class="card">
        <h2 class="text-xl font-bold mb-4">Usage Statistics</h2>

        <div v-if="usage" class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ usage.total_messages }}</div>
            <div class="text-sm text-gray-400">Messages</div>
          </div>

          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ usage.conversations_count }}</div>
            <div class="text-sm text-gray-400">Conversations</div>
          </div>

          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ usage.agents_spawned }}</div>
            <div class="text-sm text-gray-400">Agents Spawned</div>
          </div>
        </div>

        <div v-else class="text-center py-8 text-gray-400">
          Loading usage statistics...
        </div>
      </div>
    </template>

    <!-- AGENTS TAB (Dev Mode only) -->
    <template v-if="devMode && activeTab === 'agents'">
      <div class="card mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">Native Agents</h2>
        </div>

        <div v-if="loadingAgents" class="text-center py-8 text-gray-400">
          Loading agents...
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="agent in nativeAgents"
            :key="agent.id"
            class="flex items-center justify-between p-3 bg-apex-darker rounded-lg"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-8 h-8 rounded-full flex items-center justify-center font-bold"
                :style="{ backgroundColor: agent.color + '20', color: agent.color }"
              >
                {{ agent.symbol }}
              </div>
              <div>
                <div class="font-medium">{{ agent.name }}</div>
                <div class="text-xs text-gray-500">
                  {{ agent.has_pac ? 'Prose + PAC' : 'Prose' }}
                </div>
              </div>
            </div>

            <div class="flex gap-2">
              <button
                @click="viewNativePrompt(agent.id)"
                class="btn-secondary text-xs px-3 py-1"
                :disabled="!agent.has_prompt"
              >
                View
              </button>
              <button
                @click="copyToCustom(agent)"
                class="btn-secondary text-xs px-3 py-1"
                :disabled="!agent.has_prompt"
              >
                Edit Copy
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">Custom Agents</h2>
          <button @click="createNewAgent" class="btn-primary text-sm">
            + Create New Agent
          </button>
        </div>

        <div v-if="customAgents.length === 0" class="text-center py-8 text-gray-400">
          No custom agents yet. Create one to get started!
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="agent in customAgents"
            :key="agent.id"
            class="flex items-center justify-between p-3 bg-apex-darker rounded-lg"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-8 h-8 rounded-full flex items-center justify-center font-bold"
                :style="{ backgroundColor: agent.color + '20', color: agent.color }"
              >
                {{ agent.symbol }}
              </div>
              <div>
                <div class="font-medium">{{ agent.name }}</div>
                <div class="text-xs text-gray-500">{{ agent.id }}</div>
              </div>
            </div>

            <div class="flex gap-2">
              <button
                @click="editCustomAgent(agent)"
                class="btn-secondary text-xs px-3 py-1"
              >
                Edit
              </button>
              <button
                @click="deleteCustomAgent(agent.id)"
                class="text-red-400 hover:text-red-300 text-xs px-3 py-1"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- PERFECTED STONES (PAC Mode only) -->
      <div v-if="pacMode" class="card mt-6 pac-message">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <span class="text-2xl">⚗</span>
            <div>
              <h2 class="text-xl font-bold text-gold" style="text-shadow: 0 0 20px rgba(255, 215, 0, 0.3);">
                The Perfected Stones
              </h2>
              <p class="text-xs text-purple-300/70">Hyperdense codices for the Adept</p>
            </div>
          </div>
          <span class="pac-badge px-3 py-1 rounded-full text-xs font-bold">
            LAYER {{ alchemyLayer }}
          </span>
        </div>

        <div v-if="pacAgents.length === 0" class="text-center py-8 text-purple-300/50">
          No perfected stones found in this realm...
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="agent in pacAgents"
            :key="agent.id + '-pac'"
            class="flex items-center justify-between p-4 rounded-lg agent-halo"
            :style="{
              backgroundColor: 'rgba(26, 10, 46, 0.8)',
              border: '1px solid rgba(255, 215, 0, 0.2)',
              color: agent.color
            }"
          >
            <div class="flex items-center gap-4">
              <div
                class="w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl"
                :style="{
                  backgroundColor: agent.color + '15',
                  color: agent.color,
                  boxShadow: `0 0 20px ${agent.color}40`
                }"
              >
                {{ agent.symbol }}
              </div>
              <div>
                <div class="font-bold text-lg" :style="{ color: agent.color }">
                  {{ agent.name }}-Ω
                </div>
                <div class="text-xs text-purple-300/60">
                  Perfected Stone · Hyperdense Codex
                </div>
              </div>
            </div>

            <div class="flex gap-2">
              <button
                @click="viewCodex(agent.id)"
                class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                style="background: rgba(255, 215, 0, 0.1); border: 1px solid rgba(255, 215, 0, 0.3); color: #FFD700;"
              >
                View Codex
              </button>
            </div>
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-purple-500/20 text-center">
          <p class="text-xs text-purple-300/40 italic">
            "The Stone that is no stone, the medicine that heals all things"
          </p>
        </div>
      </div>
    </template>

    <!-- IMPORT TAB (Dev Mode only) -->
    <template v-if="devMode && activeTab === 'import'">
      <div class="card mb-6">
        <h2 class="text-xl font-bold mb-4">Import from Local ApexAurum</h2>
        <p class="text-gray-400 text-sm mb-6">
          Import your conversations and memory from the local ApexAurum app.
          Files are typically located in the <code class="bg-apex-darker px-2 py-1 rounded">sandbox/</code> folder.
        </p>

        <div class="space-y-6">
          <!-- Conversations Import -->
          <div class="bg-apex-darker rounded-lg p-4">
            <div class="flex items-start gap-4">
              <div class="text-3xl">💬</div>
              <div class="flex-1">
                <h3 class="font-medium mb-1">Conversations</h3>
                <p class="text-xs text-gray-500 mb-3">
                  Upload your <code>sandbox/conversations.json</code> file to import chat history.
                </p>
                <input
                  type="file"
                  accept=".json"
                  @change="handleConversationsImport"
                  class="hidden"
                  id="conversations-input"
                />
                <label
                  for="conversations-input"
                  class="btn-secondary text-sm cursor-pointer inline-block"
                  :class="{ 'opacity-50 cursor-not-allowed': importing }"
                >
                  {{ importing ? 'Importing...' : 'Select File' }}
                </label>
                <span
                  v-if="importResult.conversations"
                  class="ml-3 text-sm"
                  :class="importResult.conversations.startsWith('Error') ? 'text-red-400' : 'text-green-400'"
                >
                  {{ importResult.conversations }}
                </span>
              </div>
            </div>
          </div>

          <!-- Memory Import -->
          <div class="bg-apex-darker rounded-lg p-4">
            <div class="flex items-start gap-4">
              <div class="text-3xl">🧠</div>
              <div class="flex-1">
                <h3 class="font-medium mb-1">Memory</h3>
                <p class="text-xs text-gray-500 mb-3">
                  Upload your <code>sandbox/memory.json</code> file to import key-value memory.
                </p>
                <input
                  type="file"
                  accept=".json"
                  @change="handleMemoryImport"
                  class="hidden"
                  id="memory-input"
                />
                <label
                  for="memory-input"
                  class="btn-secondary text-sm cursor-pointer inline-block"
                  :class="{ 'opacity-50 cursor-not-allowed': importing }"
                >
                  Select File
                </label>
                <span
                  v-if="importResult.memory"
                  class="ml-3 text-sm"
                  :class="importResult.memory.startsWith('Error') ? 'text-red-400' : 'text-green-400'"
                >
                  {{ importResult.memory }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6 p-4 bg-gold/5 border border-gold/20 rounded-lg">
          <h4 class="font-medium text-gold mb-2">Supported Formats</h4>
          <ul class="text-xs text-gray-400 space-y-1">
            <li>• <strong>conversations.json</strong> - Chat history with messages</li>
            <li>• <strong>memory.json</strong> - Key-value pairs with metadata</li>
            <li>• Exported JSON files from the cloud app</li>
          </ul>
        </div>
      </div>
    </template>

    <!-- ADVANCED TAB (Dev Mode only) -->
    <template v-if="devMode && activeTab === 'advanced'">
      <div class="card mb-6">
        <h2 class="text-xl font-bold mb-4">Model Settings</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-2">Default Model</label>
            <select v-model="preferences.default_model" class="input">
              <option v-for="model in models" :key="model.id" :value="model.id">
                {{ model.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-2">
              Max Tokens: {{ preferences.max_tokens }}
            </label>
            <input
              type="range"
              v-model.number="preferences.max_tokens"
              min="256"
              max="8192"
              step="256"
              class="w-full"
            />
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-2">
              Temperature: {{ preferences.temperature }}
            </label>
            <input
              type="range"
              v-model.number="preferences.temperature"
              min="0"
              max="1"
              step="0.1"
              class="w-full"
            />
          </div>
        </div>
      </div>

      <div class="card mb-6">
        <h2 class="text-xl font-bold mb-4">Context & Cache</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-2">Cache Strategy</label>
            <select v-model="preferences.cache_strategy" class="input">
              <option v-for="s in cacheStrategies" :key="s.id" :value="s.id">
                {{ s.name }}
              </option>
            </select>
            <p class="text-xs text-gray-500 mt-1">
              Higher caching = more cost savings but potentially stale responses
            </p>
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-2">Context Strategy</label>
            <select v-model="preferences.context_strategy" class="input">
              <option v-for="s in contextStrategies" :key="s.id" :value="s.id">
                {{ s.name }}
              </option>
            </select>
            <p class="text-xs text-gray-500 mt-1">
              How to handle long conversations approaching token limits
            </p>
          </div>

          <button
            @click="savePreferences"
            class="btn-primary"
            :disabled="loading"
          >
            {{ loading ? 'Saving...' : 'Save Settings' }}
          </button>
        </div>
      </div>

      <!-- Usage Stats (in Advanced tab for dev mode) -->
      <div class="card">
        <h2 class="text-xl font-bold mb-4">Usage Statistics</h2>

        <div v-if="usage" class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ usage.total_messages }}</div>
            <div class="text-sm text-gray-400">Messages</div>
          </div>

          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ usage.conversations_count }}</div>
            <div class="text-sm text-gray-400">Conversations</div>
          </div>

          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ usage.agents_spawned }}</div>
            <div class="text-sm text-gray-400">Agents Spawned</div>
          </div>

          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ usage.music_generated }}</div>
            <div class="text-sm text-gray-400">Music Generated</div>
          </div>

          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ (usage.total_tokens / 1000).toFixed(1) }}K</div>
            <div class="text-sm text-gray-400">Tokens Used</div>
          </div>

          <div class="bg-apex-darker rounded-lg p-4">
            <div class="text-2xl font-bold text-gold">{{ formatCost(usage.total_cost_usd) }}</div>
            <div class="text-sm text-gray-400">Total Cost</div>
          </div>
        </div>

        <div v-else class="text-center py-8 text-gray-400">
          Loading usage statistics...
        </div>
      </div>
    </template>

    <!-- API TAB (Dev Mode only - placeholder) -->
    <template v-if="devMode && activeTab === 'api'">
      <div class="card">
        <h2 class="text-xl font-bold mb-4">API Settings</h2>

        <div class="text-center py-12 text-gray-400">
          <div class="text-4xl mb-4">Coming Soon</div>
          <p>API key management, webhooks, and integrations</p>
        </div>
      </div>
    </template>

    <!-- Danger Zone (shown in both modes) -->
    <div v-if="activeTab === 'profile' || !devMode" class="card mt-6 border-red-500/30">
      <h2 class="text-xl font-bold text-red-400 mb-4">Danger Zone</h2>
      <p class="text-sm text-gray-400 mb-4">
        These actions are irreversible. Please be careful.
      </p>
      <div class="flex gap-3">
        <button class="btn bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500/30">
          Delete Account
        </button>
        <button
          v-if="devMode"
          @click="devMode = false; localStorage.removeItem('devMode')"
          class="btn-secondary text-sm"
        >
          Exit Dev Mode
        </button>
      </div>
    </div>

    <!-- Prompt Viewer Modal -->
    <div v-if="showPromptViewer" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-4xl max-h-[80vh] flex flex-col">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg"
              :style="{ backgroundColor: viewingPrompt?.color + '20', color: viewingPrompt?.color }"
            >
              {{ viewingPrompt?.symbol }}
            </div>
            <div>
              <h2 class="text-xl font-bold">{{ viewingPrompt?.name }}</h2>
              <div class="text-xs text-gray-500">{{ viewingPrompt?.type }} format</div>
            </div>
          </div>
          <button @click="showPromptViewer = false" class="text-gray-400 hover:text-white text-2xl">
            &times;
          </button>
        </div>

        <div class="flex-1 overflow-y-auto">
          <pre class="bg-apex-darker rounded-lg p-4 text-sm text-gray-300 whitespace-pre-wrap font-mono">{{ viewingPrompt?.prompt }}</pre>
        </div>

        <div class="flex justify-end gap-3 mt-4 pt-4 border-t border-apex-border">
          <button @click="copyToCustom(viewingPrompt); showPromptViewer = false" class="btn-primary">
            Edit Copy
          </button>
          <button @click="showPromptViewer = false" class="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Agent Editor Modal -->
    <div v-if="showAgentEditor" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold">
            {{ editingAgent?.id ? 'Edit Agent' : 'Create Agent' }}
          </h2>
          <button @click="showAgentEditor = false" class="text-gray-400 hover:text-white text-2xl">
            &times;
          </button>
        </div>

        <div class="flex-1 overflow-y-auto space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-400 mb-2">Name</label>
              <input v-model="editingAgent.name" class="input" placeholder="Agent name" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-gray-400 mb-2">Symbol</label>
                <input v-model="editingAgent.symbol" class="input" maxlength="2" placeholder="+" />
              </div>

              <div>
                <label class="block text-sm text-gray-400 mb-2">Color</label>
                <input type="color" v-model="editingAgent.color" class="input h-10" />
              </div>
            </div>
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-2">Prompt</label>
            <textarea
              v-model="editingAgent.prompt"
              class="input h-80 resize-none font-mono text-sm"
              placeholder="Enter the system prompt for this agent..."
            ></textarea>
          </div>
        </div>

        <div class="flex justify-end gap-3 mt-4 pt-4 border-t border-apex-border">
          <button @click="showAgentEditor = false" class="btn-secondary">
            Cancel
          </button>
          <button @click="saveAgent" class="btn-primary">
            Save Agent
          </button>
        </div>
      </div>
    </div>

    <!-- Codex Viewer Modal (PAC Mode) -->
    <div v-if="showCodexViewer" class="fixed inset-0 flex items-center justify-center z-50 p-4" style="background: rgba(10, 6, 18, 0.95);">
      <div class="w-full max-w-5xl max-h-[90vh] flex flex-col rounded-xl overflow-hidden" style="background: linear-gradient(180deg, rgba(26, 10, 46, 0.98) 0%, rgba(18, 8, 31, 0.98) 100%); border: 1px solid rgba(255, 215, 0, 0.3); box-shadow: 0 0 60px rgba(255, 215, 0, 0.1);">
        <!-- Header -->
        <div class="p-6 border-b border-purple-500/20">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div
                class="w-14 h-14 rounded-full flex items-center justify-center font-bold text-2xl agent-halo"
                :style="{
                  backgroundColor: viewingCodex?.color + '15',
                  color: viewingCodex?.color,
                  boxShadow: `0 0 30px ${viewingCodex?.color}50`
                }"
              >
                {{ viewingCodex?.symbol }}
              </div>
              <div>
                <h2 class="text-2xl font-bold text-gold" style="text-shadow: 0 0 20px rgba(255, 215, 0, 0.4);">
                  {{ viewingCodex?.name }}-Ω
                </h2>
                <div class="text-sm text-purple-300/60">Hyperdense Codex · Perfected Stone</div>
              </div>
            </div>
            <button @click="showCodexViewer = false" class="text-purple-300/50 hover:text-gold text-3xl transition-colors">
              &times;
            </button>
          </div>
        </div>

        <!-- Codex Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <pre class="codex-viewer rounded-lg p-6 text-sm whitespace-pre-wrap overflow-x-auto" style="tab-size: 2;">{{ viewingCodex?.prompt }}</pre>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-purple-500/20 flex justify-between items-center">
          <p class="text-xs text-purple-300/40 italic">
            "That which is above is like that which is below"
          </p>
          <button
            @click="showCodexViewer = false"
            class="px-6 py-2 rounded-lg font-medium transition-all"
            style="background: rgba(255, 215, 0, 0.1); border: 1px solid rgba(255, 215, 0, 0.3); color: #FFD700;"
          >
            Close Codex
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
