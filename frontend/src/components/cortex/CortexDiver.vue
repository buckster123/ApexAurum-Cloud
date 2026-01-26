<script setup>
/**
 * Cortex Diver - The IDE Experience
 *
 * A full-featured code editor with AI integration, activated in dev mode.
 * "Dive deep into the code"
 */

import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useFilesStore } from '@/stores/files'
import { useCortexStore } from '@/stores/cortex'
import { useSound } from '@/composables/useSound'
import FileTabs from './FileTabs.vue'
import MonacoEditor from './MonacoEditor.vue'

const props = defineProps({
  folderId: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['exit-cortex'])

const filesStore = useFilesStore()
const cortex = useCortexStore()
const { playTone } = useSound()

// Local refs
const editorRef = ref(null)
const sidebarWidth = ref(240)
const agentPanelWidth = ref(320)
const showAgentPanel = ref(false)
const statusMessage = ref('')

// Computed
const activeTab = computed(() =>
  cortex.openTabs.find(t => t.id === cortex.activeTabId)
)

const activeContent = computed(() =>
  cortex.fileContents[cortex.activeTabId] || ''
)

const activeLanguage = computed(() =>
  cortex.fileLanguages[cortex.activeTabId] || 'plaintext'
)

// Sound effects
const cortexSounds = {
  tabOpen: () => playTone(659, 0.08, 'sine', 0.15),
  tabClose: () => playTone(440, 0.08, 'sine', 0.1),
  save: () => playTone(880, 0.1, 'sine', 0.2),
  error: () => playTone(220, 0.15, 'sawtooth', 0.15),
}

// File operations
async function openFile(file) {
  // Check if already open
  const existingTab = cortex.openTabs.find(t => t.id === file.id)
  if (existingTab) {
    cortex.setActiveTab(file.id)
    return
  }

  // Load file content
  try {
    await cortex.openFile(file)
    cortexSounds.tabOpen()
    statusMessage.value = `Opened ${file.name}`
    setTimeout(() => statusMessage.value = '', 2000)
  } catch (e) {
    cortexSounds.error()
    statusMessage.value = `Failed to open ${file.name}`
  }
}

function closeTab(tabId) {
  const tab = cortex.openTabs.find(t => t.id === tabId)
  if (tab?.isDirty) {
    if (!confirm(`${tab.name} has unsaved changes. Close anyway?`)) {
      return
    }
  }
  cortex.closeTab(tabId)
  cortexSounds.tabClose()
}

function closeAllTabs() {
  const dirtyTabs = cortex.openTabs.filter(t => t.isDirty)
  if (dirtyTabs.length > 0) {
    if (!confirm(`${dirtyTabs.length} file(s) have unsaved changes. Close all anyway?`)) {
      return
    }
  }
  cortex.closeAllTabs()
}

async function saveFile() {
  if (!cortex.activeTabId) return

  try {
    await cortex.saveFile(cortex.activeTabId)
    cortexSounds.save()
    statusMessage.value = 'Saved'
    setTimeout(() => statusMessage.value = '', 1500)
  } catch (e) {
    cortexSounds.error()
    statusMessage.value = `Save failed: ${e.message}`
  }
}

function handleContentChange(content) {
  if (cortex.activeTabId) {
    cortex.setFileContent(cortex.activeTabId, content)
  }
}

function handleSelectionChange(selection) {
  cortex.setSelection(selection)

  // If action is 'ask-agent', open the agent panel
  if (selection.action === 'ask-agent' && selection.text) {
    showAgentPanel.value = true
    // Future: Send to agent
  }
}

function handleCursorChange(cursor) {
  cortex.setCursor(cursor)
}

// Keyboard shortcuts
function handleKeyboard(event) {
  // Ctrl+S - Save
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault()
    saveFile()
    return
  }

  // Ctrl+W - Close tab
  if ((event.ctrlKey || event.metaKey) && event.key === 'w') {
    event.preventDefault()
    if (cortex.activeTabId) {
      closeTab(cortex.activeTabId)
    }
    return
  }

  // Ctrl+Shift+A - Ask agent
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'A') {
    event.preventDefault()
    showAgentPanel.value = true
    return
  }

  // Escape - Exit cortex (if no tabs open)
  if (event.key === 'Escape' && cortex.openTabs.length === 0) {
    emit('exit-cortex')
    return
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyboard)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard)
})

// Load initial directory
watch(() => props.folderId, async (folderId) => {
  await filesStore.fetchDirectory(folderId)
}, { immediate: true })
</script>

<template>
  <div class="h-screen flex flex-col bg-apex-dark text-white overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-apex-darker border-b border-apex-border">
      <div class="flex items-center gap-3">
        <span class="text-gold font-bold">CORTEX DIVER</span>
        <span class="text-gray-500 text-sm">// Deep Code Immersion</span>
      </div>

      <div class="flex items-center gap-4">
        <!-- Status message -->
        <span v-if="statusMessage" class="text-sm text-amber-400">{{ statusMessage }}</span>

        <!-- Cursor position -->
        <span v-if="cortex.cursor" class="text-xs text-gray-500 font-mono">
          Ln {{ cortex.cursor.line }}, Col {{ cortex.cursor.column }}
        </span>

        <!-- Exit button -->
        <button
          @click="emit('exit-cortex')"
          class="text-gray-400 hover:text-white text-sm"
        >
          Exit Cortex
        </button>
      </div>
    </div>

    <!-- Main content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar - File Tree -->
      <div
        class="flex flex-col border-r border-apex-border bg-apex-darker overflow-hidden"
        :style="{ width: `${sidebarWidth}px` }"
      >
        <!-- Sidebar header -->
        <div class="flex items-center justify-between px-3 py-2 border-b border-apex-border">
          <span class="text-xs text-gray-400 uppercase tracking-wider">Explorer</span>
          <button
            @click="filesStore.fetchDirectory(folderId)"
            class="text-gray-500 hover:text-gray-300"
            title="Refresh"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        <!-- Breadcrumb -->
        <div class="flex items-center gap-1 px-3 py-1 text-xs text-gray-500 border-b border-apex-border/50">
          <button
            @click="filesStore.navigateToRoot()"
            class="hover:text-gold"
          >
            ~
          </button>
          <template v-for="folder in filesStore.folderPath" :key="folder.id">
            <span class="text-gray-600">/</span>
            <button
              @click="filesStore.navigateToFolder(folder.id)"
              class="hover:text-gold truncate max-w-20"
            >
              {{ folder.name }}
            </button>
          </template>
        </div>

        <!-- File list -->
        <div class="flex-1 overflow-y-auto py-1">
          <!-- Parent folder -->
          <button
            v-if="filesStore.currentFolder"
            @click="filesStore.navigateUp()"
            class="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-gray-400 hover:bg-apex-border/30 hover:text-white"
          >
            <span class="text-xs">↑</span>
            <span>..</span>
          </button>

          <!-- Folders -->
          <button
            v-for="folder in filesStore.sortedFolders"
            :key="folder.id"
            @click="filesStore.navigateToFolder(folder.id)"
            class="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-gray-300 hover:bg-apex-border/30 hover:text-white"
          >
            <span class="text-amber-500">📁</span>
            <span class="truncate">{{ folder.name }}</span>
          </button>

          <!-- Files -->
          <button
            v-for="file in filesStore.sortedFiles"
            :key="file.id"
            @click="openFile(file)"
            @dblclick="openFile(file)"
            class="w-full flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-apex-border/30 transition-colors"
            :class="{
              'bg-amber-900/20 text-amber-200': cortex.activeTabId === file.id,
              'text-gray-300 hover:text-white': cortex.activeTabId !== file.id,
            }"
          >
            <span>{{ filesStore.getFileIcon(file.file_type) }}</span>
            <span class="truncate">{{ file.name }}</span>
            <span
              v-if="cortex.openTabs.find(t => t.id === file.id)?.isDirty"
              class="w-1.5 h-1.5 rounded-full bg-amber-500 ml-auto"
            ></span>
          </button>
        </div>
      </div>

      <!-- Editor area -->
      <div class="flex-1 flex flex-col min-w-0">
        <!-- File tabs -->
        <FileTabs
          :tabs="cortex.openTabs"
          :active-tab-id="cortex.activeTabId"
          @select="cortex.setActiveTab"
          @close="closeTab"
          @close-all="closeAllTabs"
        />

        <!-- Editor -->
        <div class="flex-1 relative">
          <MonacoEditor
            v-if="activeTab"
            ref="editorRef"
            :model-value="activeContent"
            :language="activeLanguage"
            :filename="activeTab?.name"
            @update:model-value="handleContentChange"
            @save="saveFile"
            @selection-change="handleSelectionChange"
            @cursor-change="handleCursorChange"
          />

          <!-- No file open state -->
          <div
            v-else
            class="absolute inset-0 flex flex-col items-center justify-center text-gray-500"
          >
            <div class="text-6xl mb-4 opacity-30">⚗️</div>
            <p class="text-lg">Select a file to begin</p>
            <p class="text-sm mt-2">
              <kbd class="px-1.5 py-0.5 bg-apex-darker rounded text-xs">Ctrl+S</kbd> save
              <span class="mx-2">·</span>
              <kbd class="px-1.5 py-0.5 bg-apex-darker rounded text-xs">Ctrl+W</kbd> close
              <span class="mx-2">·</span>
              <kbd class="px-1.5 py-0.5 bg-apex-darker rounded text-xs">Ctrl+Shift+A</kbd> ask agent
            </p>
          </div>
        </div>
      </div>

      <!-- Agent panel (collapsible) -->
      <div
        v-if="showAgentPanel"
        class="flex flex-col border-l border-apex-border bg-apex-darker"
        :style="{ width: `${agentPanelWidth}px` }"
      >
        <div class="flex items-center justify-between px-3 py-2 border-b border-apex-border">
          <span class="text-xs text-amber-400 uppercase tracking-wider">Agent</span>
          <button
            @click="showAgentPanel = false"
            class="text-gray-500 hover:text-gray-300"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Agent content -->
        <div class="flex-1 p-3 overflow-y-auto">
          <div v-if="cortex.selection?.text" class="mb-4">
            <p class="text-xs text-gray-500 mb-1">Selected code:</p>
            <pre class="text-xs bg-apex-dark p-2 rounded overflow-x-auto max-h-32">{{ cortex.selection.text }}</pre>
          </div>

          <div class="text-center text-gray-500 py-8">
            <p class="text-sm">Agent integration coming soon</p>
            <p class="text-xs mt-1">Select code and ask questions</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Status bar -->
    <div class="flex items-center justify-between px-4 py-1 bg-apex-darker border-t border-apex-border text-xs text-gray-500">
      <div class="flex items-center gap-4">
        <span v-if="activeTab">{{ activeLanguage }}</span>
        <span v-if="activeTab">{{ activeTab.isDirty ? 'Modified' : 'Saved' }}</span>
      </div>
      <div class="flex items-center gap-4">
        <span>UTF-8</span>
        <span>{{ cortex.openTabs.length }} file(s) open</span>
      </div>
    </div>
  </div>
</template>
