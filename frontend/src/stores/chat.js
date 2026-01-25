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

  // Getters
  const sortedConversations = computed(() => {
    const convs = conversations.value || []
    if (!Array.isArray(convs)) return []
    return [...convs].sort((a, b) =>
      new Date(b.updated_at) - new Date(a.updated_at)
    )
  })

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

  async function sendMessage(content, agent = 'CLAUDE', model = 'claude-3-haiku-20240307', usePac = false) {
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
          model,
          agent,
          stream: true,
          use_pac: usePac
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

  return {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    streamingContent,
    sortedConversations,
    fetchConversations,
    loadConversation,
    createConversation,
    sendMessage,
    deleteConversation,
    updateConversation,
  }
})
