<script setup>
/**
 * NurseryView - Model Training Studio
 *
 * The Nursery: where training data is cultivated and models are raised.
 * Session A delivers a functional Data Garden (Tab 1).
 * Tabs 2-5 are placeholders for future sessions.
 */

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useNurseryStore } from '@/stores/nursery'
import api from '@/services/api'

const nursery = useNurseryStore()

// ---------------------------------------------------------------------------
// Tab state
// ---------------------------------------------------------------------------
const activeTab = ref('garden')
const tabs = [
  { id: 'garden', label: 'Data Garden' },
  { id: 'forge', label: 'Training Forge' },
  { id: 'cradle', label: 'Model Cradle' },
  { id: 'apprentices', label: 'Apprentices' },
  { id: 'feed', label: 'Village Feed' },
]

// ---------------------------------------------------------------------------
// Generate form state
// ---------------------------------------------------------------------------
const selectedTools = ref([])
const numExamples = ref(50)
const variationLevel = ref('medium')
const datasetName = ref('')
const generateError = ref('')

// ---------------------------------------------------------------------------
// Extract form state
// ---------------------------------------------------------------------------
const extractTools = ref([])
const minExamples = ref(10)
const extractName = ref('')
const extractError = ref('')

// ---------------------------------------------------------------------------
// Available tools (fetched from backend)
// ---------------------------------------------------------------------------
const availableTools = ref([])
const loadingTools = ref(false)

// ---------------------------------------------------------------------------
// Preview / expand state
// ---------------------------------------------------------------------------
const expandedDataset = ref(null)
const previewData = ref(null)
const loadingPreview = ref(false)

// ---------------------------------------------------------------------------
// Confirm delete
// ---------------------------------------------------------------------------
const confirmDelete = ref(null)
const confirmModelDelete = ref(null)

// Apprentice Protocol state
const masterAgent = ref('AZOTH')
const apprenticeName = ref('')
const specialization = ref('')
const autoGenerate = ref(false)
const apprenticeNumExamples = ref(50)
const apprenticeError = ref('')
const apprenticeSuccess = ref('')
const confirmApprenticeDelete = ref(null)

const masterAgents = [
  { id: 'AZOTH', label: 'Azoth', color: 'text-[#D4AF37]', bg: 'bg-[#D4AF37]/10 border-[#D4AF37]/30' },
  { id: 'ELYSIAN', label: 'Elysian', color: 'text-[#9B59B6]', bg: 'bg-[#9B59B6]/10 border-[#9B59B6]/30' },
  { id: 'VAJRA', label: 'Vajra', color: 'text-[#E74C3C]', bg: 'bg-[#E74C3C]/10 border-[#E74C3C]/30' },
  { id: 'KETHER', label: 'Kether', color: 'text-[#3498DB]', bg: 'bg-[#3498DB]/10 border-[#3498DB]/30' },
]

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------
const totalDatasets = computed(() => nursery.stats.datasets || nursery.datasets.length)
const totalExamples = computed(() => {
  if (nursery.stats.total_examples) return nursery.stats.total_examples
  return nursery.datasets.reduce((sum, d) => sum + (d.num_examples || 0), 0)
})

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(async () => {
  await nursery.fetchDatasets()
  await fetchAvailableTools()
  await nursery.fetchStats()
  // Also check Together key + fetch jobs if on forge tab
  await nursery.checkTogetherKey()
})

// Watch for tab changes to manage polling
watch(activeTab, (newTab) => {
  if (newTab === 'forge') {
    startJobPolling()
    nursery.fetchTrainingJobs()
    if (!nursery.trainableModels.length) nursery.fetchTrainableModels()
  } else if (newTab === 'cradle') {
    stopJobPolling()
    nursery.fetchModels()
  } else if (newTab === 'apprentices') {
    stopJobPolling()
    nursery.fetchApprentices()
  } else if (newTab === 'feed') {
    stopJobPolling()
    nursery.fetchVillageActivity()
  } else {
    stopJobPolling()
  }
})

onUnmounted(() => {
  stopJobPolling()
})

// ---------------------------------------------------------------------------
// Fetch available tools from backend
// ---------------------------------------------------------------------------
async function fetchAvailableTools() {
  loadingTools.value = true
  try {
    const response = await api.get('/api/v1/tools')
    if (response.data) {
      availableTools.value = response.data.tools || response.data || []
    }
  } catch (e) {
    console.error('Failed to fetch tools:', e)
    availableTools.value = []
  } finally {
    loadingTools.value = false
  }
}

// ---------------------------------------------------------------------------
// Tool selection helpers
// ---------------------------------------------------------------------------
function toggleTool(toolName, list) {
  // list may be a ref (from script) or unwrapped array (from template)
  const arr = Array.isArray(list) ? list : list.value
  const idx = arr.indexOf(toolName)
  if (idx === -1) {
    arr.push(toolName)
  } else {
    arr.splice(idx, 1)
  }
}

function isToolSelected(toolName, list) {
  const arr = Array.isArray(list) ? list : list.value
  return arr.includes(toolName)
}

function getToolDisplayName(tool) {
  if (typeof tool === 'string') return tool
  return tool.name || tool.tool_name || tool.id || 'unknown'
}

// ---------------------------------------------------------------------------
// Generate synthetic data
// ---------------------------------------------------------------------------
async function handleGenerate() {
  if (selectedTools.value.length === 0) {
    generateError.value = 'Select at least one tool.'
    return
  }

  generateError.value = ''
  try {
    await nursery.generateData(
      selectedTools.value,
      numExamples.value,
      variationLevel.value,
      datasetName.value || null,
    )
    // Reset form on success
    selectedTools.value = []
    numExamples.value = 50
    variationLevel.value = 'medium'
    datasetName.value = ''
  } catch (e) {
    generateError.value = e.response?.data?.detail || e.message || 'Generation failed. Please try again.'
  }
}

// ---------------------------------------------------------------------------
// Extract from conversations
// ---------------------------------------------------------------------------
async function handleExtract() {
  extractError.value = ''
  try {
    await nursery.extractData(
      extractTools.value.length > 0 ? extractTools.value : null,
      minExamples.value,
      extractName.value || null,
    )
    // Reset form on success
    extractTools.value = []
    minExamples.value = 10
    extractName.value = ''
  } catch (e) {
    extractError.value = e.response?.data?.detail || e.message || 'Extraction failed. Please try again.'
  }
}

// ---------------------------------------------------------------------------
// Delete dataset
// ---------------------------------------------------------------------------
async function handleDelete(datasetId) {
  if (confirmDelete.value === datasetId) {
    await nursery.deleteDataset(datasetId)
    confirmDelete.value = null
    expandedDataset.value = null
    previewData.value = null
  } else {
    confirmDelete.value = datasetId
    setTimeout(() => {
      confirmDelete.value = null
    }, 3000)
  }
}

// ---------------------------------------------------------------------------
// Preview / expand dataset
// ---------------------------------------------------------------------------
async function toggleExpand(dataset) {
  if (expandedDataset.value === dataset.id) {
    expandedDataset.value = null
    previewData.value = null
    return
  }

  expandedDataset.value = dataset.id
  loadingPreview.value = true
  try {
    const response = await api.get(`/api/v1/nursery/datasets/${dataset.id}`)
    previewData.value = response.data
  } catch (e) {
    console.error('Failed to load preview:', e)
    previewData.value = null
  } finally {
    loadingPreview.value = false
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function getSourceColor(source) {
  if (source === 'synthetic') return 'bg-green-500/20 text-green-400'
  if (source === 'extracted') return 'bg-blue-500/20 text-blue-400'
  return 'bg-gray-500/20 text-gray-400'
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatRelativeDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`

  return date.toLocaleDateString()
}

// ---------------------------------------------------------------------------
// Training Forge state
// ---------------------------------------------------------------------------
const forgeDataset = ref('')
const forgeModel = ref('meta-llama/Llama-3.2-3B-Instruct')
const forgeEpochs = ref(3)
const forgeLearningRate = ref('1e-5')
const forgeLora = ref(true)
const forgeBatchSize = ref('')
const forgeSuffix = ref('')
const forgeError = ref('')
const forgeSuccess = ref('')

let jobPollInterval = null

// Training Forge lifecycle
const forgeModels = [
  { id: 'meta-llama/Llama-3.2-1B-Instruct', label: 'Llama 3.2 1B', size: '1B' },
  { id: 'meta-llama/Llama-3.2-3B-Instruct', label: 'Llama 3.2 3B', size: '3B' },
  { id: 'meta-llama/Meta-Llama-3.1-8B-Instruct-Reference', label: 'Llama 3.1 8B', size: '8B' },
  { id: 'Qwen/Qwen2.5-7B-Instruct', label: 'Qwen 2.5 7B', size: '7B' },
]

const learningRates = [
  { value: '1e-4', label: '1e-4 (aggressive)' },
  { value: '5e-5', label: '5e-5 (moderate)' },
  { value: '1e-5', label: '1e-5 (default)' },
  { value: '5e-6', label: '5e-6 (gentle)' },
]

// Computed for forge stats
const runningJobs = computed(() => nursery.trainingJobs.filter(j => j.status === 'running' || j.status === 'uploading' || j.status === 'pending').length)
const completedJobs = computed(() => nursery.trainingJobs.filter(j => j.status === 'completed').length)
const failedJobs = computed(() => nursery.trainingJobs.filter(j => j.status === 'failed').length)

// ---------------------------------------------------------------------------
// Training Forge actions
// ---------------------------------------------------------------------------
async function handleEstimate() {
  if (!forgeDataset.value) return
  try {
    await nursery.estimateCost(
      forgeDataset.value,
      forgeModel.value,
      forgeEpochs.value,
      forgeLora.value,
    )
  } catch (e) {
    console.error('Estimate failed:', e)
  }
}

async function handleStartTraining() {
  if (!forgeDataset.value) {
    forgeError.value = 'Select a dataset first.'
    return
  }
  if (!nursery.hasTogetherKey) {
    forgeError.value = 'Together.ai API key required. Configure in Settings > API Keys.'
    return
  }

  forgeError.value = ''
  forgeSuccess.value = ''
  try {
    const result = await nursery.startTraining(
      forgeDataset.value,
      forgeModel.value,
      forgeEpochs.value,
      parseFloat(forgeLearningRate.value),
      forgeLora.value,
      forgeBatchSize.value ? parseInt(forgeBatchSize.value) : null,
      forgeSuffix.value || null,
    )
    forgeSuccess.value = result.message || 'Training started!'
    // Reset some fields
    forgeSuffix.value = ''
    forgeBatchSize.value = ''
  } catch (e) {
    forgeError.value = e.response?.data?.detail || e.message || 'Failed to start training.'
  }
}

async function handleCancelJob(jobId) {
  await nursery.cancelJob(jobId)
}

function startJobPolling() {
  stopJobPolling()
  jobPollInterval = setInterval(async () => {
    if (activeTab.value === 'forge') {
      await nursery.fetchTrainingJobs()
    }
  }, 15000)
}

function stopJobPolling() {
  if (jobPollInterval) {
    clearInterval(jobPollInterval)
    jobPollInterval = null
  }
}

function getStatusColor(status) {
  const colors = {
    pending: 'bg-gray-500/20 text-gray-400',
    uploading: 'bg-blue-500/20 text-blue-400',
    running: 'bg-amber-500/20 text-amber-400',
    completed: 'bg-green-500/20 text-green-400',
    failed: 'bg-red-500/20 text-red-400',
  }
  return colors[status] || 'bg-gray-500/20 text-gray-400'
}

function getModelLabel(modelId) {
  const found = forgeModels.find(m => m.id === modelId)
  return found ? found.label : modelId?.split('/').pop() || modelId
}

// ---------------------------------------------------------------------------
// Model Cradle helpers
// ---------------------------------------------------------------------------
function getModelTypeColor(type) {
  const colors = {
    lora_adapter: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    cloud_hosted: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    uploaded: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  }
  return colors[type] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
}

function getModelTypeLabel(type) {
  const labels = { lora_adapter: 'LoRA', cloud_hosted: 'Cloud', uploaded: 'Uploaded' }
  return labels[type] || type
}

async function handleModelDelete(modelId) {
  if (confirmModelDelete.value === modelId) {
    await nursery.deleteModel(modelId)
    confirmModelDelete.value = null
  } else {
    confirmModelDelete.value = modelId
    setTimeout(() => { confirmModelDelete.value = null }, 3000)
  }
}

async function handleRegister(modelId) {
  try {
    await nursery.registerModel(modelId)
  } catch (e) {
    console.error('Registration failed:', e)
  }
}

// ---------------------------------------------------------------------------
// Village Feed helpers
// ---------------------------------------------------------------------------
async function handleDiscover() {
  await nursery.discoverModels(nursery.discoveryQuery)
}

function getActivityIcon(type) {
  return type === 'training_job' ? '&#9881;' : '&#9733;'
}

function getActivityColor(item) {
  if (item.type === 'model_created') return item.village_posted ? 'text-green-400' : 'text-cyan-400'
  const colors = { completed: 'text-green-400', running: 'text-amber-400', failed: 'text-red-400', pending: 'text-gray-400' }
  return colors[item.status] || 'text-gray-400'
}

function formatRelativeTime(isoStr) {
  if (!isoStr) return ''
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

// ---------------------------------------------------------------------------
// Apprentice Protocol helpers
// ---------------------------------------------------------------------------
function getApprenticeStatusColor(status) {
  const colors = {
    dataset_ready: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    training: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    trained: 'bg-green-500/20 text-green-400 border-green-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
  }
  return colors[status] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
}

function getApprenticeStatusLabel(status) {
  const labels = { dataset_ready: 'Ready', training: 'Training', trained: 'Trained', failed: 'Failed' }
  return labels[status] || status
}

function getMasterColor(agent) {
  const found = masterAgents.find(m => m.id === agent)
  return found ? found.color : 'text-gray-400'
}

async function handleCreateApprentice() {
  if (!apprenticeName.value.trim()) {
    apprenticeError.value = 'Apprentice name is required.'
    return
  }
  apprenticeError.value = ''
  apprenticeSuccess.value = ''
  try {
    const result = await nursery.createApprentice(
      masterAgent.value,
      apprenticeName.value.trim(),
      specialization.value.trim() || null,
      autoGenerate.value,
      apprenticeNumExamples.value,
    )
    apprenticeSuccess.value = result.message || 'Apprentice created!'
    apprenticeName.value = ''
    specialization.value = ''
    autoGenerate.value = false
    apprenticeNumExamples.value = 50
  } catch (e) {
    apprenticeError.value = e.response?.data?.detail || e.message || 'Failed to create apprentice.'
  }
}

async function handleDeleteApprentice(id) {
  if (confirmApprenticeDelete.value === id) {
    await nursery.deleteApprentice(id)
    confirmApprenticeDelete.value = null
  } else {
    confirmApprenticeDelete.value = id
    setTimeout(() => { confirmApprenticeDelete.value = null }, 3000)
  }
}

async function handleAutoTrain(apprentice) {
  if (!nursery.hasTogetherKey) return
  try {
    await nursery.startTraining(
      apprentice.dataset_id,
      'meta-llama/Llama-3.2-3B-Instruct',
      3, 1e-5, true, null, null, apprentice.id
    )
    await nursery.fetchApprentices()
  } catch (e) {
    console.error('Auto-train failed:', e)
  }
}
</script>

<template>
  <div class="min-h-screen bg-apex-dark text-white pt-20 px-4">
    <div class="max-w-6xl mx-auto">

      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-serif text-gold">The Nursery</h1>
        <p class="text-gray-400 mt-1">Model Training Studio</p>
      </div>

      <!-- Tier Gate -->
      <div v-if="nursery.tierRequired" class="card border-amber-500/30 bg-amber-500/5 mb-8">
        <h2 class="text-xl font-bold text-amber-400 mb-2">Adept Tier Required</h2>
        <p class="text-gray-400 mb-4">
          The Nursery is available to Adept-tier subscribers ($30/mo).
          Train models, generate datasets, and raise apprentice minds.
        </p>
        <router-link
          to="/billing"
          class="inline-block px-6 py-2 bg-gold text-black font-bold rounded-lg hover:bg-gold/90 transition-colors"
        >
          Upgrade to Adept
        </router-link>
      </div>

      <!-- Tab Bar -->
      <div v-if="!nursery.tierRequired" class="flex gap-4 mb-8 border-b border-apex-border overflow-x-auto">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="pb-3 px-2 whitespace-nowrap transition-colors"
          :class="activeTab === tab.id
            ? 'text-gold border-b-2 border-gold'
            : 'text-gray-400 hover:text-white'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab content (hidden when tier-gated) -->
      <template v-if="!nursery.tierRequired">
      <!-- ================================================================= -->
      <!-- Tab 1: Data Garden (functional)                                    -->
      <!-- ================================================================= -->
      <div v-if="activeTab === 'garden'">
        <div class="grid lg:grid-cols-2 gap-6">

          <!-- LEFT SECTION: Generate & Extract -->
          <div class="space-y-6">

            <!-- Generate Card -->
            <div class="card">
              <h2 class="text-xl font-bold mb-4">Generate Synthetic Data</h2>

              <!-- Tool multi-select -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Tools</label>
                <div v-if="loadingTools" class="text-sm text-gray-500 py-2">
                  Loading tools...
                </div>
                <div v-else-if="availableTools.length === 0" class="text-sm text-gray-500 py-2">
                  No tools available
                </div>
                <div v-else class="max-h-48 overflow-y-auto border border-apex-border rounded-lg p-3 bg-apex-darker space-y-2">
                  <label
                    v-for="tool in availableTools"
                    :key="getToolDisplayName(tool)"
                    class="flex items-center gap-2 cursor-pointer hover:bg-white/5 rounded px-2 py-1 transition-colors"
                  >
                    <input
                      type="checkbox"
                      :checked="isToolSelected(getToolDisplayName(tool), selectedTools)"
                      @change="toggleTool(getToolDisplayName(tool), selectedTools)"
                      class="accent-gold w-4 h-4"
                    />
                    <span class="text-sm text-gray-300">{{ getToolDisplayName(tool) }}</span>
                  </label>
                </div>
                <div v-if="selectedTools.length > 0" class="text-xs text-gray-500 mt-1">
                  {{ selectedTools.length }} tool{{ selectedTools.length !== 1 ? 's' : '' }} selected
                </div>
              </div>

              <!-- Examples slider -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">
                  Examples: <span class="text-white font-medium">{{ numExamples }}</span>
                </label>
                <input
                  type="range"
                  v-model.number="numExamples"
                  min="10"
                  max="500"
                  step="10"
                  class="w-full accent-gold"
                />
                <div class="flex justify-between text-xs text-gray-500 mt-1">
                  <span>10</span>
                  <span>500</span>
                </div>
              </div>

              <!-- Variation radio buttons -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Variation</label>
                <div class="flex gap-3">
                  <label
                    v-for="level in ['low', 'medium', 'high']"
                    :key="level"
                    class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all"
                    :class="variationLevel === level
                      ? 'bg-gold/20 ring-1 ring-gold'
                      : 'bg-apex-darker hover:bg-white/5'"
                  >
                    <input
                      type="radio"
                      :value="level"
                      v-model="variationLevel"
                      class="accent-gold"
                    />
                    <span class="text-sm capitalize">{{ level }}</span>
                  </label>
                </div>
              </div>

              <!-- Dataset name -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Dataset Name (optional)</label>
                <input
                  v-model="datasetName"
                  type="text"
                  class="input"
                  placeholder="e.g., web-tools-v1"
                />
              </div>

              <!-- Generate error -->
              <div
                v-if="generateError"
                class="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm"
              >
                {{ generateError }}
              </div>

              <!-- Generate button -->
              <button
                @click="handleGenerate"
                :disabled="nursery.generating || selectedTools.length === 0"
                class="btn-primary w-full flex items-center justify-center gap-2"
              >
                <svg
                  v-if="nursery.generating"
                  class="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ nursery.generating ? 'Generating...' : 'Generate' }}
              </button>
            </div>

            <!-- Extract Card -->
            <div class="card">
              <h2 class="text-xl font-bold mb-4">Extract from Conversations</h2>

              <!-- Tool filter (optional) -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Tool Filter (optional)</label>
                <div v-if="loadingTools" class="text-sm text-gray-500 py-2">
                  Loading tools...
                </div>
                <div v-else-if="availableTools.length === 0" class="text-sm text-gray-500 py-2">
                  No tools available
                </div>
                <div v-else class="max-h-36 overflow-y-auto border border-apex-border rounded-lg p-3 bg-apex-darker space-y-2">
                  <label
                    v-for="tool in availableTools"
                    :key="'ext-' + getToolDisplayName(tool)"
                    class="flex items-center gap-2 cursor-pointer hover:bg-white/5 rounded px-2 py-1 transition-colors"
                  >
                    <input
                      type="checkbox"
                      :checked="isToolSelected(getToolDisplayName(tool), extractTools)"
                      @change="toggleTool(getToolDisplayName(tool), extractTools)"
                      class="accent-gold w-4 h-4"
                    />
                    <span class="text-sm text-gray-300">{{ getToolDisplayName(tool) }}</span>
                  </label>
                </div>
                <div v-if="extractTools.length > 0" class="text-xs text-gray-500 mt-1">
                  {{ extractTools.length }} tool{{ extractTools.length !== 1 ? 's' : '' }} selected
                </div>
              </div>

              <!-- Min examples -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Min Examples</label>
                <input
                  v-model.number="minExamples"
                  type="number"
                  min="1"
                  max="1000"
                  class="input"
                  placeholder="10"
                />
              </div>

              <!-- Dataset name -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Dataset Name (optional)</label>
                <input
                  v-model="extractName"
                  type="text"
                  class="input"
                  placeholder="e.g., conversation-extract-01"
                />
              </div>

              <!-- Extract error -->
              <div
                v-if="extractError"
                class="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm"
              >
                {{ extractError }}
              </div>

              <!-- Extract button -->
              <button
                @click="handleExtract"
                :disabled="nursery.extracting"
                class="btn-primary w-full flex items-center justify-center gap-2"
              >
                <svg
                  v-if="nursery.extracting"
                  class="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ nursery.extracting ? 'Extracting...' : 'Extract' }}
              </button>
            </div>
          </div>

          <!-- RIGHT SECTION: Dataset List -->
          <div>
            <!-- Stats Bar -->
            <div class="grid grid-cols-2 gap-4 mb-6">
              <div class="card p-4 text-center">
                <div class="text-2xl font-bold text-gold">{{ totalDatasets }}</div>
                <div class="text-sm text-gray-400">Datasets</div>
              </div>
              <div class="card p-4 text-center">
                <div class="text-2xl font-bold text-gold">{{ totalExamples.toLocaleString() }}</div>
                <div class="text-sm text-gray-400">Total Examples</div>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="nursery.loading" class="text-center py-12 text-gray-400">
              Loading datasets...
            </div>

            <!-- Empty State -->
            <div v-else-if="nursery.datasets.length === 0" class="text-center py-12">
              <div class="text-4xl mb-4 text-gray-600">{ }</div>
              <h2 class="text-xl font-bold mb-2">No datasets yet</h2>
              <p class="text-gray-400">
                Generate or extract training data to get started.
              </p>
            </div>

            <!-- Dataset Cards -->
            <div v-else class="space-y-4">
              <div
                v-for="dataset in nursery.datasets"
                :key="dataset.id"
                class="card hover:border-gold/30 transition-colors cursor-pointer"
                @click="toggleExpand(dataset)"
              >
                <!-- Header row -->
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center gap-2 min-w-0">
                    <h3 class="font-medium truncate">{{ dataset.name || 'Untitled Dataset' }}</h3>
                    <span
                      :class="getSourceColor(dataset.source)"
                      class="text-xs px-2 py-0.5 rounded-full whitespace-nowrap"
                    >
                      {{ dataset.source || 'unknown' }}
                    </span>
                  </div>

                  <!-- Delete button -->
                  <button
                    @click.stop="handleDelete(dataset.id)"
                    class="ml-2 px-2 py-1 rounded text-sm transition-colors flex-shrink-0"
                    :class="confirmDelete === dataset.id
                      ? 'bg-red-500/30 text-red-300'
                      : 'text-gray-500 hover:text-red-400 hover:bg-red-500/20'"
                  >
                    {{ confirmDelete === dataset.id ? 'Confirm?' : 'Delete' }}
                  </button>
                </div>

                <!-- Tool tags -->
                <div v-if="dataset.tool_names?.length" class="flex flex-wrap gap-1 mb-2">
                  <span
                    v-for="tool in dataset.tool_names"
                    :key="tool"
                    class="text-xs bg-gold/10 text-gold px-2 py-0.5 rounded"
                  >
                    {{ tool }}
                  </span>
                </div>

                <!-- Stats line -->
                <div class="text-sm text-gray-400">
                  {{ dataset.num_examples || 0 }} examples
                  <span v-if="dataset.size_bytes"> &middot; {{ formatSize(dataset.size_bytes) }}</span>
                </div>

                <!-- Created date -->
                <div class="text-xs text-gray-500 mt-1">
                  {{ formatRelativeDate(dataset.created_at) }}
                </div>

                <!-- Expanded Preview -->
                <div
                  v-if="expandedDataset === dataset.id"
                  class="mt-4 pt-4 border-t border-apex-border"
                  @click.stop
                >
                  <div v-if="loadingPreview" class="text-sm text-gray-400 py-2">
                    Loading preview...
                  </div>
                  <div v-else-if="previewData?.examples?.length" class="space-y-2">
                    <div class="text-xs text-gray-500 mb-2">
                      Preview (first {{ Math.min(previewData.examples.length, 5) }} examples)
                    </div>
                    <div
                      v-for="(example, idx) in previewData.examples.slice(0, 5)"
                      :key="idx"
                      class="bg-apex-darker rounded p-3 text-sm"
                    >
                      <div v-if="example.input" class="mb-1">
                        <span class="text-gray-500">Input:</span>
                        <span class="text-gray-300 ml-1">{{ example.input }}</span>
                      </div>
                      <div v-if="example.output">
                        <span class="text-gray-500">Output:</span>
                        <span class="text-gray-300 ml-1">{{ example.output }}</span>
                      </div>
                      <div v-if="example.tool_name" class="text-xs text-gold/60 mt-1">
                        Tool: {{ example.tool_name }}
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-gray-500 py-2">
                    No preview data available.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ================================================================= -->
      <!-- Tab 2: Training Forge (functional)                                 -->
      <!-- ================================================================= -->
      <div v-if="activeTab === 'forge'">
        <div class="grid lg:grid-cols-2 gap-6">

          <!-- LEFT: New Training Job -->
          <div class="space-y-6">
            <div class="card">
              <h2 class="text-xl font-bold mb-4">New Training Job</h2>

              <!-- No Together key warning -->
              <div v-if="!nursery.hasTogetherKey" class="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <p class="text-amber-400 text-sm font-medium mb-1">Together.ai API Key Required</p>
                <p class="text-gray-400 text-xs mb-2">Training runs on Together.ai GPUs using your API key.</p>
                <router-link to="/settings" class="text-gold text-xs hover:underline">
                  Configure in Settings &rarr;
                </router-link>
              </div>

              <!-- Dataset selector -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Dataset</label>
                <select
                  v-model="forgeDataset"
                  class="input w-full"
                  @change="handleEstimate"
                >
                  <option value="">Select a dataset...</option>
                  <option
                    v-for="ds in nursery.datasets"
                    :key="ds.id"
                    :value="ds.id"
                  >
                    {{ ds.name }} ({{ ds.num_examples }} examples)
                  </option>
                </select>
                <div v-if="nursery.datasets.length === 0" class="text-xs text-gray-500 mt-1">
                  No datasets yet. Generate one in the Data Garden tab.
                </div>
              </div>

              <!-- Base model selector -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Base Model</label>
                <div class="grid grid-cols-2 gap-2">
                  <label
                    v-for="model in forgeModels"
                    :key="model.id"
                    class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all"
                    :class="forgeModel === model.id
                      ? 'bg-gold/20 ring-1 ring-gold'
                      : 'bg-apex-darker hover:bg-white/5'"
                  >
                    <input
                      type="radio"
                      :value="model.id"
                      v-model="forgeModel"
                      @change="handleEstimate"
                      class="accent-gold"
                    />
                    <div>
                      <div class="text-sm">{{ model.label }}</div>
                      <div class="text-xs text-gray-500">{{ model.size }} params</div>
                    </div>
                  </label>
                </div>
              </div>

              <!-- Config section -->
              <div class="mb-4 grid grid-cols-2 gap-4">
                <!-- Epochs -->
                <div>
                  <label class="block text-sm text-gray-400 mb-2">
                    Epochs: <span class="text-white">{{ forgeEpochs }}</span>
                  </label>
                  <input
                    type="range"
                    v-model.number="forgeEpochs"
                    min="1"
                    max="10"
                    @change="handleEstimate"
                    class="w-full accent-gold"
                  />
                  <div class="flex justify-between text-xs text-gray-500">
                    <span>1</span>
                    <span>10</span>
                  </div>
                </div>

                <!-- Learning rate -->
                <div>
                  <label class="block text-sm text-gray-400 mb-2">Learning Rate</label>
                  <select v-model="forgeLearningRate" class="input w-full">
                    <option v-for="lr in learningRates" :key="lr.value" :value="lr.value">
                      {{ lr.label }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- LoRA toggle -->
              <div class="mb-4 flex items-center gap-3">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="forgeLora"
                    @change="handleEstimate"
                    class="accent-gold w-4 h-4"
                  />
                  <span class="text-sm">LoRA (recommended)</span>
                </label>
                <span class="text-xs text-gray-500">
                  {{ forgeLora ? 'Faster, cheaper, memory-efficient' : 'Full fine-tune -- slower, higher quality' }}
                </span>
              </div>

              <!-- Optional: suffix + batch -->
              <div class="mb-4 grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm text-gray-400 mb-2">Suffix (optional)</label>
                  <input v-model="forgeSuffix" class="input" placeholder="e.g., v1" />
                </div>
                <div>
                  <label class="block text-sm text-gray-400 mb-2">Batch Size</label>
                  <select v-model="forgeBatchSize" class="input w-full">
                    <option value="">Auto</option>
                    <option value="4">4</option>
                    <option value="8">8</option>
                    <option value="16">16</option>
                    <option value="32">32</option>
                  </select>
                </div>
              </div>

              <!-- Cost estimate -->
              <div v-if="nursery.costEstimate" class="mb-4 p-3 bg-gold/5 border border-gold/20 rounded-lg">
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-400">Estimated Cost</span>
                  <span class="text-lg font-bold text-gold">
                    ${{ nursery.costEstimate.estimated_cost_usd?.toFixed(2) }}
                  </span>
                </div>
                <div class="text-xs text-gray-500 mt-1">
                  {{ nursery.costEstimate.total_tokens?.toLocaleString() }} tokens
                  &middot; ~{{ nursery.costEstimate.estimated_minutes }} min
                  &middot; {{ nursery.costEstimate.training_method }}
                </div>
              </div>
              <div v-else-if="nursery.estimating" class="mb-4 text-sm text-gray-400">
                Calculating estimate...
              </div>

              <!-- Error/Success -->
              <div v-if="forgeError" class="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {{ forgeError }}
              </div>
              <div v-if="forgeSuccess" class="mb-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg text-green-400 text-sm">
                {{ forgeSuccess }}
              </div>

              <!-- Start Training button -->
              <button
                @click="handleStartTraining"
                :disabled="nursery.startingTraining || !forgeDataset || !nursery.hasTogetherKey"
                class="btn-primary w-full flex items-center justify-center gap-2"
                :class="{ 'opacity-50 cursor-not-allowed': !forgeDataset || !nursery.hasTogetherKey }"
              >
                <svg
                  v-if="nursery.startingTraining"
                  class="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ nursery.startingTraining ? 'Starting...' : 'Start Training' }}
              </button>
            </div>
          </div>

          <!-- RIGHT: Active Jobs -->
          <div>
            <!-- Job stats -->
            <div class="grid grid-cols-3 gap-4 mb-6">
              <div class="card p-4 text-center">
                <div class="text-2xl font-bold text-gold">{{ nursery.trainingJobs.length }}</div>
                <div class="text-sm text-gray-400">Total Jobs</div>
              </div>
              <div class="card p-4 text-center">
                <div class="text-2xl font-bold text-amber-400">{{ runningJobs }}</div>
                <div class="text-sm text-gray-400">Active</div>
              </div>
              <div class="card p-4 text-center">
                <div class="text-2xl font-bold text-green-400">{{ completedJobs }}</div>
                <div class="text-sm text-gray-400">Completed</div>
              </div>
            </div>

            <!-- Loading -->
            <div v-if="nursery.loadingJobs" class="text-center py-12 text-gray-400">
              Loading jobs...
            </div>

            <!-- Empty -->
            <div v-else-if="nursery.trainingJobs.length === 0" class="text-center py-12">
              <div class="text-4xl mb-4 text-gray-600">{ }</div>
              <h2 class="text-xl font-bold mb-2">No training jobs yet</h2>
              <p class="text-gray-400">
                Select a dataset and start a training job.
              </p>
            </div>

            <!-- Job cards -->
            <div v-else class="space-y-4">
              <div
                v-for="job in nursery.trainingJobs"
                :key="job.id"
                class="card"
              >
                <!-- Header -->
                <div class="flex items-start justify-between mb-2">
                  <div>
                    <h3 class="font-medium">{{ job.dataset_name || 'Training Job' }}</h3>
                    <div class="text-sm text-gray-400">{{ getModelLabel(job.base_model) }}</div>
                  </div>
                  <span
                    :class="getStatusColor(job.status)"
                    class="text-xs px-2 py-0.5 rounded-full capitalize"
                  >
                    {{ job.status }}
                  </span>
                </div>

                <!-- Progress bar (for running jobs) -->
                <div v-if="job.status === 'running' || job.status === 'uploading'" class="mb-3">
                  <div class="h-2 bg-apex-darker rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-500"
                      :class="job.status === 'uploading' ? 'bg-blue-500' : 'bg-amber-500'"
                      :style="{ width: `${job.progress || 5}%` }"
                    />
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    {{ job.progress ? `${Math.round(job.progress)}%` : 'Starting...' }}
                  </div>
                </div>

                <!-- Cost -->
                <div v-if="job.cost_estimate" class="text-sm text-gray-400 mb-1">
                  Est. ${{ job.cost_estimate?.toFixed(2) }}
                  <span v-if="job.cost_actual"> &rarr; Actual: ${{ job.cost_actual?.toFixed(2) }}</span>
                </div>

                <!-- Timestamps -->
                <div class="text-xs text-gray-500">
                  Created {{ formatRelativeDate(job.created_at) }}
                  <span v-if="job.started_at"> &middot; Started {{ formatRelativeDate(job.started_at) }}</span>
                  <span v-if="job.completed_at"> &middot; Done {{ formatRelativeDate(job.completed_at) }}</span>
                </div>

                <!-- Output model name -->
                <div v-if="job.output_name && job.status === 'completed'" class="text-xs text-green-400 mt-1">
                  Model: {{ job.output_name }}
                </div>

                <!-- Error message -->
                <div v-if="job.error_message" class="text-xs text-red-400 mt-1">
                  {{ job.error_message }}
                </div>

                <!-- Cancel button -->
                <div v-if="job.status === 'pending' || job.status === 'running' || job.status === 'uploading'" class="mt-3">
                  <button
                    @click="handleCancelJob(job.id)"
                    class="text-xs text-red-400 hover:text-red-300 transition-colors"
                  >
                    Cancel Job
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- ================================================================= -->
      <!-- Tab 3: Model Cradle                                                -->
      <!-- ================================================================= -->
        <!-- Tab 3: Model Cradle -->
        <div v-if="activeTab === 'cradle'" class="space-y-6">
          <!-- Stats bar -->
          <div class="flex items-center gap-4 text-sm">
            <div class="bg-apex-card border border-apex-border rounded-lg px-4 py-2">
              <span class="text-gray-400">Models:</span>
              <span class="text-white font-bold ml-1">{{ nursery.models.length }}</span>
            </div>
            <div class="bg-apex-card border border-apex-border rounded-lg px-4 py-2">
              <span class="text-gray-400">In Village:</span>
              <span class="text-green-400 font-bold ml-1">{{ nursery.models.filter(m => m.village_posted).length }}</span>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="nursery.loadingModels" class="text-center py-16">
            <div class="animate-spin h-8 w-8 border-2 border-gold border-t-transparent rounded-full mx-auto mb-3"></div>
            <p class="text-gray-400">Loading models...</p>
          </div>

          <!-- Empty state -->
          <div v-else-if="!nursery.models.length" class="text-center py-16">
            <div class="text-5xl text-gray-600 mb-4">&#10697;</div>
            <h3 class="text-lg font-bold text-gray-300 mb-2">No Trained Models Yet</h3>
            <p class="text-gray-500 max-w-md mx-auto mb-4">
              Models appear here when training jobs complete. Start a training job in the Forge tab.
            </p>
            <button @click="activeTab = 'forge'" class="text-gold hover:text-gold-bright text-sm">
              Go to Training Forge &rarr;
            </button>
          </div>

          <!-- Model cards grid -->
          <div v-else class="grid md:grid-cols-2 gap-4">
            <div
              v-for="model in nursery.models"
              :key="model.id"
              class="bg-apex-card border border-apex-border rounded-xl p-5 hover:border-gold/30 transition-colors"
            >
              <!-- Header -->
              <div class="flex items-start justify-between mb-3">
                <div>
                  <h3 class="font-bold text-white">{{ model.name }}</h3>
                  <p class="text-sm text-gray-400">{{ model.base_model?.split('/').pop() || 'Unknown base' }}</p>
                </div>
                <span
                  :class="getModelTypeColor(model.model_type)"
                  class="text-xs px-2 py-1 rounded-full border"
                >
                  {{ getModelTypeLabel(model.model_type) }}
                </span>
              </div>

              <!-- Capabilities -->
              <div v-if="model.capabilities?.length" class="flex flex-wrap gap-1 mb-3">
                <span
                  v-for="cap in model.capabilities.slice(0, 5)"
                  :key="cap"
                  class="text-xs bg-gold/10 text-gold px-2 py-0.5 rounded"
                >
                  {{ cap }}
                </span>
                <span v-if="model.capabilities.length > 5" class="text-xs text-gray-500">
                  +{{ model.capabilities.length - 5 }} more
                </span>
              </div>

              <!-- Performance -->
              <div v-if="model.performance" class="text-xs text-gray-500 mb-3">
                <span v-if="model.performance.final_loss">Loss: {{ model.performance.final_loss }}</span>
                <span v-if="model.performance.events_count"> &middot; {{ model.performance.events_count }} events</span>
              </div>

              <!-- Footer -->
              <div class="flex items-center justify-between pt-3 border-t border-apex-border">
                <span class="text-xs text-gray-500">{{ formatRelativeTime(model.created_at) }}</span>
                <div class="flex items-center gap-2">
                  <!-- Village status -->
                  <button
                    v-if="model.village_posted"
                    disabled
                    class="text-xs bg-green-500/10 text-green-400 px-3 py-1 rounded-lg border border-green-500/30"
                  >
                    &#10003; In Village
                  </button>
                  <button
                    v-else
                    @click="handleRegister(model.id)"
                    class="text-xs bg-gold/10 text-gold px-3 py-1 rounded-lg border border-gold/30 hover:bg-gold/20 transition-colors"
                  >
                    Register in Village
                  </button>
                  <!-- Delete -->
                  <button
                    @click="handleModelDelete(model.id)"
                    :class="confirmModelDelete === model.id ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-apex-dark text-gray-500 border-apex-border hover:text-red-400 hover:border-red-500/30'"
                    class="text-xs px-3 py-1 rounded-lg border transition-colors"
                  >
                    {{ confirmModelDelete === model.id ? 'Confirm?' : 'Delete' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

      <!-- ================================================================= -->
      <!-- Tab 4: Apprentices (placeholder)                                   -->
      <!-- ================================================================= -->
        <!-- Tab 4: Apprentices -->
        <div v-if="activeTab === 'apprentices'" class="space-y-6">
          <div class="grid lg:grid-cols-2 gap-6">

            <!-- Left: Create Apprentice Form -->
            <div class="bg-apex-card border border-apex-border rounded-xl p-6">
              <h3 class="text-lg font-bold text-white mb-4">Create Apprentice</h3>

              <!-- Master Agent Selector -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Master Agent</label>
                <div class="grid grid-cols-2 gap-2">
                  <button
                    v-for="agent in masterAgents"
                    :key="agent.id"
                    @click="masterAgent = agent.id"
                    :class="masterAgent === agent.id ? agent.bg + ' border' : 'bg-apex-dark border border-apex-border hover:border-gray-500'"
                    class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    <span :class="agent.color">{{ agent.label }}</span>
                  </button>
                </div>
              </div>

              <!-- Apprentice Name -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Apprentice Name</label>
                <input
                  v-model="apprenticeName"
                  type="text"
                  placeholder="e.g., Search Scholar"
                  class="input w-full"
                  :disabled="nursery.creatingApprentice"
                />
              </div>

              <!-- Specialization -->
              <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">Specialization</label>
                <input
                  v-model="specialization"
                  type="text"
                  placeholder="e.g., web_search, cortex_recall"
                  class="input w-full"
                  :disabled="nursery.creatingApprentice"
                />
                <p class="text-xs text-gray-500 mt-1">Comma-separated tool names for training data</p>
              </div>

              <!-- Auto-Generate Toggle -->
              <div class="mb-4">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    v-model="autoGenerate"
                    type="checkbox"
                    class="w-4 h-4 rounded bg-apex-dark border-apex-border accent-gold"
                    :disabled="nursery.creatingApprentice"
                  />
                  <span class="text-sm text-gray-300">Auto-generate training dataset</span>
                </label>
              </div>

              <!-- Num Examples (shown when auto-generate is on) -->
              <div v-if="autoGenerate" class="mb-4">
                <label class="block text-sm text-gray-400 mb-2">
                  Training Examples: <span class="text-white font-bold">{{ apprenticeNumExamples }}</span>
                </label>
                <input
                  v-model.number="apprenticeNumExamples"
                  type="range"
                  min="10"
                  max="500"
                  step="10"
                  class="w-full accent-gold"
                />
                <div class="flex justify-between text-xs text-gray-500 mt-1">
                  <span>10</span>
                  <span>250</span>
                  <span>500</span>
                </div>
              </div>

              <!-- Messages -->
              <div v-if="apprenticeError" class="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm mb-4">
                {{ apprenticeError }}
              </div>
              <div v-if="apprenticeSuccess" class="bg-green-500/10 border border-green-500/50 rounded-lg p-3 text-green-400 text-sm mb-4">
                {{ apprenticeSuccess }}
              </div>

              <!-- Create Button -->
              <button
                @click="handleCreateApprentice"
                :disabled="nursery.creatingApprentice || !apprenticeName.trim()"
                class="w-full py-2.5 bg-gold text-black font-bold rounded-lg hover:bg-gold/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ nursery.creatingApprentice ? 'Creating...' : 'Create Apprentice' }}
              </button>
            </div>

            <!-- Right: Apprentice List -->
            <div>
              <!-- Stats bar -->
              <div class="flex items-center gap-3 mb-4 text-sm">
                <div class="bg-apex-card border border-apex-border rounded-lg px-3 py-1.5">
                  <span class="text-gray-400">Total:</span>
                  <span class="text-white font-bold ml-1">{{ nursery.apprentices.length }}</span>
                </div>
                <div class="bg-apex-card border border-apex-border rounded-lg px-3 py-1.5">
                  <span class="text-gray-400">Training:</span>
                  <span class="text-amber-400 font-bold ml-1">{{ nursery.apprentices.filter(a => a.status === 'training').length }}</span>
                </div>
                <div class="bg-apex-card border border-apex-border rounded-lg px-3 py-1.5">
                  <span class="text-gray-400">Trained:</span>
                  <span class="text-green-400 font-bold ml-1">{{ nursery.apprentices.filter(a => a.status === 'trained').length }}</span>
                </div>
              </div>

              <!-- Loading -->
              <div v-if="nursery.loadingApprentices" class="text-center py-12">
                <div class="animate-spin h-8 w-8 border-2 border-gold border-t-transparent rounded-full mx-auto mb-3"></div>
                <p class="text-gray-400">Loading apprentices...</p>
              </div>

              <!-- Empty state -->
              <div v-else-if="!nursery.apprentices.length" class="text-center py-12 bg-apex-card border border-apex-border rounded-xl">
                <div class="text-5xl text-gray-600 mb-4">&#9734;</div>
                <h3 class="text-lg font-bold text-gray-300 mb-2">No Apprentices Yet</h3>
                <p class="text-gray-500 max-w-sm mx-auto">
                  Create an apprentice to begin raising a new mind under one of the four masters.
                </p>
              </div>

              <!-- Apprentice cards -->
              <div v-else class="space-y-3">
                <div
                  v-for="a in nursery.apprentices"
                  :key="a.id"
                  class="bg-apex-card border border-apex-border rounded-xl p-4 hover:border-gold/20 transition-colors"
                >
                  <!-- Header -->
                  <div class="flex items-start justify-between mb-2">
                    <div>
                      <h4 class="font-bold text-white">{{ a.apprentice_name }}</h4>
                      <p class="text-sm">
                        <span class="text-gray-500">Master:</span>
                        <span :class="getMasterColor(a.master_agent)" class="font-medium ml-1">{{ a.master_agent }}</span>
                      </p>
                    </div>
                    <span
                      :class="getApprenticeStatusColor(a.status)"
                      class="text-xs px-2 py-1 rounded-full border"
                    >
                      {{ getApprenticeStatusLabel(a.status) }}
                    </span>
                  </div>

                  <!-- Specialization -->
                  <p v-if="a.specialization" class="text-xs text-gray-400 mb-2">
                    Specialization: <span class="text-gray-300">{{ a.specialization }}</span>
                  </p>

                  <!-- Dataset / Model info -->
                  <div class="text-xs text-gray-500 space-y-1 mb-3">
                    <div v-if="a.dataset_name">
                      Dataset: <span class="text-gray-300">{{ a.dataset_name }}</span>
                      <span class="text-gray-600">({{ a.num_examples }} examples)</span>
                    </div>
                    <div v-if="a.model_name">
                      Model: <span class="text-green-400">{{ a.model_name }}</span>
                    </div>
                  </div>

                  <!-- Footer -->
                  <div class="flex items-center justify-between pt-2 border-t border-apex-border">
                    <span class="text-xs text-gray-500">{{ formatRelativeTime(a.created_at) }}</span>
                    <div class="flex items-center gap-2">
                      <!-- Start Training button (only for dataset_ready with Together key) -->
                      <button
                        v-if="a.status === 'dataset_ready' && a.dataset_id && nursery.hasTogetherKey"
                        @click="handleAutoTrain(a)"
                        class="text-xs bg-gold/10 text-gold px-3 py-1 rounded-lg border border-gold/30 hover:bg-gold/20 transition-colors"
                      >
                        Start Training
                      </button>
                      <span
                        v-if="a.status === 'dataset_ready' && !nursery.hasTogetherKey"
                        class="text-xs text-gray-500 italic"
                      >
                        Needs Together.ai key
                      </span>
                      <!-- Delete -->
                      <button
                        @click="handleDeleteApprentice(a.id)"
                        :class="confirmApprenticeDelete === a.id ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-apex-dark text-gray-500 border-apex-border hover:text-red-400 hover:border-red-500/30'"
                        class="text-xs px-3 py-1 rounded-lg border transition-colors"
                      >
                        {{ confirmApprenticeDelete === a.id ? 'Confirm?' : 'Delete' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>

      <!-- ================================================================= -->
      <!-- Tab 5: Village Feed                                                -->
      <!-- ================================================================= -->
        <!-- Tab 5: Village Feed -->
        <div v-if="activeTab === 'feed'" class="space-y-8">

          <!-- Activity Feed -->
          <div>
            <h3 class="text-lg font-bold text-white mb-4">Recent Activity</h3>

            <div v-if="nursery.loadingActivity" class="text-center py-8">
              <div class="animate-spin h-6 w-6 border-2 border-gold border-t-transparent rounded-full mx-auto"></div>
            </div>

            <div v-else-if="!nursery.villageActivity.length" class="text-center py-8">
              <p class="text-gray-500">No nursery activity yet. Generate datasets or start training to see events here.</p>
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="item in nursery.villageActivity"
                :key="item.type + '-' + item.id"
                class="bg-apex-card border border-apex-border rounded-lg px-4 py-3 flex items-center gap-3"
              >
                <!-- Icon -->
                <div
                  :class="getActivityColor(item)"
                  class="text-lg flex-shrink-0"
                  v-html="getActivityIcon(item.type)"
                ></div>
                <!-- Message -->
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-gray-200 truncate">{{ item.message }}</p>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span v-if="item.agent_id" class="text-xs text-gold/70">{{ item.agent_id }}</span>
                    <span v-if="item.status && item.type === 'training_job'" :class="getStatusColor(item.status)" class="text-xs px-1.5 py-0.5 rounded">
                      {{ item.status }}
                    </span>
                  </div>
                </div>
                <!-- Timestamp -->
                <span class="text-xs text-gray-500 flex-shrink-0">{{ formatRelativeTime(item.timestamp) }}</span>
              </div>
            </div>
          </div>

          <!-- Model Discovery -->
          <div>
            <h3 class="text-lg font-bold text-white mb-4">Discover Models</h3>
            <div class="flex gap-2 mb-4">
              <input
                v-model="nursery.discoveryQuery"
                type="text"
                placeholder="Search Village for models..."
                class="input flex-1"
                @keyup.enter="handleDiscover"
              />
              <button
                @click="handleDiscover"
                :disabled="nursery.loadingDiscovery"
                class="px-4 py-2 bg-gold/10 text-gold border border-gold/30 rounded-lg hover:bg-gold/20 transition-colors text-sm"
              >
                {{ nursery.loadingDiscovery ? 'Searching...' : 'Search' }}
              </button>
            </div>

            <div v-if="nursery.loadingDiscovery" class="text-center py-6">
              <div class="animate-spin h-6 w-6 border-2 border-gold border-t-transparent rounded-full mx-auto"></div>
            </div>

            <div v-else-if="nursery.discoveredModels.length" class="space-y-2">
              <div
                v-for="(item, idx) in nursery.discoveredModels"
                :key="idx"
                class="bg-apex-card border border-apex-border rounded-lg px-4 py-3"
              >
                <p class="text-sm text-gray-200">{{ item.content || item.text || JSON.stringify(item) }}</p>
                <div class="flex items-center gap-2 mt-1">
                  <span v-if="item.agent_id" class="text-xs text-gold/70">{{ item.agent_id }}</span>
                  <span v-if="item.created_at" class="text-xs text-gray-500">{{ formatRelativeTime(item.created_at) }}</span>
                </div>
              </div>
            </div>

            <div v-else class="text-center py-6">
              <p class="text-gray-500 text-sm">No shared models found. Register models in the Model Cradle to share them.</p>
            </div>
          </div>

        </div>
      </template>

    </div>
  </div>
</template>
