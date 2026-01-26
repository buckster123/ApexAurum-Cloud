import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useChatStore = defineStore('chat', () => {
  // State
  const conversations = ref([])
  const currentConversation = ref(null)
  const messages = ref([])
  const isStreaming = ref(false)
  const streamingContent = ref('')

  // ═══════════════════════════════════════════════════════════════════════════════
  // MODEL SELECTION - Unleash the Stones
  // ═══════════════════════════════════════════════════════════════════════════════
  const availableModels = ref([])
  const defaultModel = ref('claude-sonnet-4-5-20250929')
  const selectedModel = ref(localStorage.getItem('apexaurum_selected_model') || 'claude-sonnet-4-5-20250929')
  const maxTokens = ref(parseInt(localStorage.getItem('apexaurum_max_tokens')) || 8192)

  // Getters
  const sortedConversations = computed(() => {
    const convs = conversations.value || []
    if (!Array.isArray(convs)) return []
    return [...convs].sort((a, b) =>
      new Date(b.updated_at) - new Date(a.updated_at)
    )
  })

  // ═══════════════════════════════════════════════════════════════════════════════
  // MODEL ACTIONS
  // ═══════════════════════════════════════════════════════════════════════════════

  async function fetchModels() {
    try {
      const response = await api.get('/api/v1/chat/models')
      availableModels.value = response.data.models || []
      defaultModel.value = response.data.default || 'claude-sonnet-4-5-20250929'

      // If selected model is not in available models, reset to default
      const modelIds = availableModels.value.map(m => m.id)
      if (!modelIds.includes(selectedModel.value)) {
        selectedModel.value = defaultModel.value
        localStorage.setItem('apexaurum_selected_model', defaultModel.value)
      }
    } catch (e) {
      console.error('Failed to fetch models:', e)
      // Keep defaults
    }
  }

  function setSelectedModel(modelId) {
    selectedModel.value = modelId
    localStorage.setItem('apexaurum_selected_model', modelId)
  }

  function setMaxTokens(tokens) {
    maxTokens.value = tokens
    localStorage.setItem('apexaurum_max_tokens', tokens.toString())
  }

  // Actions
  async function fetchConversations() {
    try {
      const response = await api.get('/api/v1/chat/conversations')
      conversations.value = response.data.conversations || []
    } catch (e) {
      console.error('Failed to fetch conversations:', e)
      conversations.value = []
    }
  }

  async function loadConversation(id) {
    try {
      const response = await api.get(`/api/v1/chat/conversations/${id}`)
      currentConversation.value = response.data
      messages.value = response.data.messages || []
    } catch (e) {
      console.error('Failed to load conversation:', e)
      currentConversation.value = null
      messages.value = []
    }
  }

  async function createConversation() {
    currentConversation.value = null
    messages.value = []
  }

  async function sendMessage(content, agent = 'CLAUDE', model = null, usePac = false) {
    // Use selected model if not specified
    const useModel = model || selectedModel.value || defaultModel.value
    // Add user message immediately
    messages.value.push({
      id: Date.now().toString(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    })

    // Start streaming
    isStreaming.value = true
    streamingContent.value = ''

    // Create placeholder for assistant message
    const assistantMsgId = Date.now().toString() + '-assistant'
    messages.value.push({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    })

    try {
      const apiUrl = import.meta.env.VITE_API_URL || ''
      const token = localStorage.getItem('accessToken')

      const response = await fetch(`${apiUrl}/api/v1/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          message: content,
          conversation_id: currentConversation.value?.id,
          model: useModel,
          agent,
          stream: true,
          use_pac: usePac,
          max_tokens: maxTokens.value,
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // Read the SSE stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE messages (ending with \n\n)
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || '' // Keep incomplete message in buffer

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue

          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'token' && data.content) {
              // Append token to streaming content and message
              streamingContent.value += data.content
              const msg = messages.value.find(m => m.id === assistantMsgId)
              if (msg) msg.content += data.content
            } else if (data.type === 'start' && data.conversation_id) {
              // Update conversation ID if new
              if (!currentConversation.value) {
                currentConversation.value = { id: data.conversation_id }
              }
            } else if (data.type === 'error') {
              throw new Error(data.message || 'Stream error')
            }
          } catch (parseError) {
            console.warn('Failed to parse SSE:', line, parseError)
          }
        }
      }

      // Fetch conversations if we got a new one
      if (currentConversation.value?.id) {
        await fetchConversations()
      }

    } catch (e) {
      console.error('Chat error:', e)
      // Update assistant message to show error
      const msg = messages.value.find(m => m.id === assistantMsgId)
      if (msg) {
        msg.role = 'system'
        msg.content = `Error: ${e.message}`
      }
    } finally {
      isStreaming.value = false
      streamingContent.value = ''
    }
  }

  async function deleteConversation(id) {
    await api.delete(`/api/v1/chat/conversations/${id}`)
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (currentConversation.value?.id === id) {
      currentConversation.value = null
      messages.value = []
    }
  }

  async function updateConversation(id, updates) {
    await api.patch(`/api/v1/chat/conversations/${id}`, updates)
    const conv = conversations.value.find(c => c.id === id)
    if (conv) {
      Object.assign(conv, updates)
    }
  }

  async function toggleFavorite(id) {
    const conv = conversations.value.find(c => c.id === id)
    if (conv) {
      await updateConversation(id, { favorite: !conv.favorite })
    }
  }

  async function archiveConversation(id) {
    const conv = conversations.value.find(c => c.id === id)
    if (conv) {
      await updateConversation(id, { archived: !conv.archived })
      // Remove from list if archived (we show non-archived by default)
      if (!conv.archived) {
        conversations.value = conversations.value.filter(c => c.id !== id)
      }
    }
  }

  async function exportConversation(id, format = 'json') {
    const apiUrl = import.meta.env.VITE_API_URL || ''
    const token = localStorage.getItem('accessToken')

    const response = await fetch(`${apiUrl}/api/v1/chat/conversations/${id}/export?format=${format}`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    })

    if (!response.ok) throw new Error('Export failed')

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // Get filename from Content-Disposition header or generate one
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = `conversation.${format === 'markdown' ? 'md' : format}`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?(.+?)"?$/)
      if (match) filename = match[1]
    }

    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // BRANCHING (THE MULTIVERSE) - Fork conversations at any message point
  // ═══════════════════════════════════════════════════════════════════════════════

  async function forkConversation(conversationId, messageId, label = null) {
    try {
      const response = await api.post(
        `/api/v1/chat/conversations/${conversationId}/fork`,
        { message_id: messageId, label }
      )
      // Refresh conversations list to show new branch
      await fetchConversations()
      return response.data
    } catch (e) {
      console.error('Failed to fork conversation:', e)
      throw e
    }
  }

  async function getBranches(conversationId) {
    try {
      const response = await api.get(
        `/api/v1/chat/conversations/${conversationId}/branches`
      )
      return response.data
    } catch (e) {
      console.error('Failed to get branches:', e)
      return { parent: null, branches: [], branch_count: 0 }
    }
  }

  return {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    streamingContent,
    sortedConversations,
    // Model selection (Unleash the Stones)
    availableModels,
    defaultModel,
    selectedModel,
    maxTokens,
    fetchModels,
    setSelectedModel,
    setMaxTokens,
    // Core actions
    fetchConversations,
    loadConversation,
    createConversation,
    sendMessage,
    deleteConversation,
    updateConversation,
    toggleFavorite,
    archiveConversation,
    exportConversation,
    // Branching (The Multiverse)
    forkConversation,
    getBranches,
  }
})
