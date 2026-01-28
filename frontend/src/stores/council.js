/**
 * Council Store - The Deliberation Chamber
 *
 * State management for multi-agent deliberation sessions.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

// Agent colors for UI consistency
export const AGENT_COLORS = {
  AZOTH: '#00ffaa',
  ELYSIAN: '#ff69b4',
  VAJRA: '#ffcc00',
  KETHER: '#9370db',
}

// Available agents for selection (4 native alchemical agents)
export const AVAILABLE_AGENTS = [
  { id: 'AZOTH', name: 'Azoth', description: 'The Alchemist - Transformation & synthesis' },
  { id: 'VAJRA', name: 'Vajra', description: 'The Thunderbolt - Direct truth & clarity' },
  { id: 'ELYSIAN', name: 'Elysian', description: 'The Muse - Creativity & inspiration' },
  { id: 'KETHER', name: 'Kether', description: 'The Crown - Wisdom & higher perspective' },
]

export const useCouncilStore = defineStore('council', () => {
  // ═══════════════════════════════════════════════════════════════════════════════
  // STATE - The Chamber's Memory
  // ═══════════════════════════════════════════════════════════════════════════════

  const sessions = ref([])
  const currentSession = ref(null)
  const isLoading = ref(false)
  const isExecutingRound = ref(false)
  const error = ref(null)

  // Form state for creating new sessions
  const newSessionTopic = ref('')
  const newSessionAgents = ref(['AZOTH', 'VAJRA', 'ELYSIAN'])
  const newSessionMaxRounds = ref(10)

  // Auto-deliberation state
  const isAutoDeliberating = ref(false)
  const autoDeliberationAbort = ref(null)  // AbortController
  const streamingRound = ref(null)  // Current round being streamed
  const streamingAgents = ref({})  // {agentId: {content, tokens}} for real-time display
  const pendingButtIn = ref('')  // Human message to inject

  // ═══════════════════════════════════════════════════════════════════════════════
  // GETTERS - Derived State
  // ═══════════════════════════════════════════════════════════════════════════════

  const sortedSessions = computed(() => {
    return [...sessions.value].sort((a, b) =>
      new Date(b.created_at) - new Date(a.created_at)
    )
  })

  const currentRounds = computed(() => {
    if (!currentSession.value?.rounds) return []
    return [...currentSession.value.rounds].sort((a, b) =>
      a.round_number - b.round_number
    )
  })

  const latestRound = computed(() => {
    const rounds = currentRounds.value
    return rounds.length > 0 ? rounds[rounds.length - 1] : null
  })

  const canExecuteRound = computed(() => {
    if (!currentSession.value) return false
    if (currentSession.value.state === 'complete') return false
    if (currentSession.value.current_round >= currentSession.value.max_rounds) return false
    return !isExecutingRound.value
  })

  const sessionProgress = computed(() => {
    if (!currentSession.value) return 0
    return (currentSession.value.current_round / currentSession.value.max_rounds) * 100
  })

  // ═══════════════════════════════════════════════════════════════════════════════
  // ACTIONS - The Chamber's Operations
  // ═══════════════════════════════════════════════════════════════════════════════

  async function fetchSessions() {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get('/api/v1/council/sessions')
      sessions.value = response.data
    } catch (e) {
      console.error('Failed to fetch sessions:', e)
      error.value = e.response?.data?.detail || 'Failed to load sessions'
      sessions.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function loadSession(sessionId) {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get(`/api/v1/council/sessions/${sessionId}`)
      currentSession.value = response.data
    } catch (e) {
      console.error('Failed to load session:', e)
      error.value = e.response?.data?.detail || 'Failed to load session'
      currentSession.value = null
    } finally {
      isLoading.value = false
    }
  }

  async function createSession() {
    if (!newSessionTopic.value.trim()) {
      error.value = 'Please enter a topic for deliberation'
      return null
    }
    if (newSessionAgents.value.length < 1) {
      error.value = 'Please select at least one agent'
      return null
    }

    isLoading.value = true
    error.value = null
    try {
      const response = await api.post('/api/v1/council/sessions', {
        topic: newSessionTopic.value.trim(),
        agents: newSessionAgents.value,
        max_rounds: newSessionMaxRounds.value,
        use_tools: false,
      })
      const session = response.data

      // Add to sessions list and set as current
      sessions.value.unshift(session)
      currentSession.value = session

      // Clear form
      newSessionTopic.value = ''

      return session
    } catch (e) {
      console.error('Failed to create session:', e)
      error.value = e.response?.data?.detail || 'Failed to create session'
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function executeRound() {
    if (!currentSession.value || !canExecuteRound.value) return null

    isExecutingRound.value = true
    error.value = null
    try {
      const response = await api.post(
        `/api/v1/council/sessions/${currentSession.value.id}/round`
      )
      const roundResult = response.data

      // Reload full session to get updated state
      await loadSession(currentSession.value.id)

      return roundResult
    } catch (e) {
      console.error('Failed to execute round:', e)
      error.value = e.response?.data?.detail || 'Failed to execute round'
      return null
    } finally {
      isExecutingRound.value = false
    }
  }

  async function deleteSession(sessionId) {
    try {
      await api.delete(`/api/v1/council/sessions/${sessionId}`)
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
      }
      return true
    } catch (e) {
      console.error('Failed to delete session:', e)
      error.value = e.response?.data?.detail || 'Failed to delete session'
      return false
    }
  }

  function clearCurrentSession() {
    currentSession.value = null
    error.value = null
  }

  function toggleAgent(agentId) {
    const index = newSessionAgents.value.indexOf(agentId)
    if (index > -1) {
      // Don't remove if it's the last agent
      if (newSessionAgents.value.length > 1) {
        newSessionAgents.value.splice(index, 1)
      }
    } else {
      newSessionAgents.value.push(agentId)
    }
  }

  function clearError() {
    error.value = null
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // AUTO-DELIBERATION ACTIONS
  // ═══════════════════════════════════════════════════════════════════════════════

  async function startAutoDeliberation(numRounds = 10) {
    if (!currentSession.value || isAutoDeliberating.value) return

    isAutoDeliberating.value = true
    isExecutingRound.value = true
    streamingRound.value = null
    streamingAgents.value = {}
    error.value = null

    const abortController = new AbortController()
    autoDeliberationAbort.value = abortController

    // Build API URL with https:// prefix
    let apiUrl = import.meta.env.VITE_API_URL || ''
    if (apiUrl && !apiUrl.startsWith('http://') && !apiUrl.startsWith('https://')) {
      apiUrl = 'https://' + apiUrl
    }

    try {
      const response = await fetch(
        `${apiUrl}/api/v1/council/sessions/${currentSession.value.id}/auto-deliberate?num_rounds=${numRounds}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          },
          signal: abortController.signal,
        }
      )

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || `HTTP ${response.status}`)
      }

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

            if (data.type === 'start') {
              console.log('Auto-deliberation started:', data)
            } else if (data.type === 'round_start') {
              streamingRound.value = data.round_number
              streamingAgents.value = {}
            } else if (data.type === 'agent_complete') {
              streamingAgents.value[data.agent_id] = {
                content: data.content,
                input_tokens: data.input_tokens,
                output_tokens: data.output_tokens,
              }
            } else if (data.type === 'human_message_injected') {
              console.log('Human message injected:', data.content)
              pendingButtIn.value = ''  // Clear the input
            } else if (data.type === 'round_complete') {
              // Update session with new round data
              if (currentSession.value) {
                currentSession.value.current_round = data.round_number
                currentSession.value.total_cost_usd = data.total_cost_usd
              }
              // Reload full session to get round details
              await loadSession(currentSession.value.id)
              streamingRound.value = null
              streamingAgents.value = {}
            } else if (data.type === 'paused') {
              console.log('Deliberation paused at round:', data.round_number)
              if (currentSession.value) {
                currentSession.value.state = 'paused'
              }
            } else if (data.type === 'stopped') {
              console.log('Deliberation stopped at round:', data.round_number)
            } else if (data.type === 'end') {
              console.log('Auto-deliberation ended:', data)
              if (currentSession.value) {
                currentSession.value.state = data.state
                currentSession.value.total_cost_usd = data.total_cost_usd
              }
              await loadSession(currentSession.value.id)
            }
          } catch (parseError) {
            console.warn('Failed to parse SSE:', line, parseError)
          }
        }
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        console.log('Auto-deliberation aborted by user')
      } else {
        console.error('Auto-deliberation error:', e)
        error.value = e.message || 'Auto-deliberation failed'
      }
    } finally {
      isAutoDeliberating.value = false
      isExecutingRound.value = false
      autoDeliberationAbort.value = null
      streamingRound.value = null
      streamingAgents.value = {}
    }
  }

  function stopAutoDeliberation() {
    // Abort the SSE stream
    if (autoDeliberationAbort.value) {
      autoDeliberationAbort.value.abort()
    }
  }

  async function pauseAutoDeliberation() {
    if (!currentSession.value) return

    try {
      await api.post(`/api/v1/council/sessions/${currentSession.value.id}/pause`)
      // The SSE stream will receive the 'paused' event
    } catch (e) {
      console.error('Failed to pause:', e)
      error.value = e.response?.data?.detail || 'Failed to pause'
    }
  }

  async function resumeAutoDeliberation(numRounds = 10) {
    if (!currentSession.value) return

    try {
      // First set state back to running
      await api.post(`/api/v1/council/sessions/${currentSession.value.id}/resume`)
      // Then start auto-deliberation again
      await startAutoDeliberation(numRounds)
    } catch (e) {
      console.error('Failed to resume:', e)
      error.value = e.response?.data?.detail || 'Failed to resume'
    }
  }

  async function stopSession() {
    if (!currentSession.value) return

    // First abort any running stream
    stopAutoDeliberation()

    try {
      await api.post(`/api/v1/council/sessions/${currentSession.value.id}/stop`)
      if (currentSession.value) {
        currentSession.value.state = 'complete'
      }
      await loadSession(currentSession.value.id)
    } catch (e) {
      console.error('Failed to stop:', e)
      error.value = e.response?.data?.detail || 'Failed to stop'
    }
  }

  async function submitButtIn() {
    if (!currentSession.value || !pendingButtIn.value.trim()) return

    try {
      await api.post(`/api/v1/council/sessions/${currentSession.value.id}/butt-in`, {
        message: pendingButtIn.value.trim(),
      })
      // Don't clear pendingButtIn here - it will be cleared when SSE confirms injection
      // Or clear it now if not in auto mode
      if (!isAutoDeliberating.value) {
        pendingButtIn.value = ''
      }
    } catch (e) {
      console.error('Failed to submit butt-in:', e)
      error.value = e.response?.data?.detail || 'Failed to submit message'
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════════════════════

  return {
    // State
    sessions,
    currentSession,
    isLoading,
    isExecutingRound,
    error,
    // Form state
    newSessionTopic,
    newSessionAgents,
    newSessionMaxRounds,
    // Auto-deliberation state
    isAutoDeliberating,
    streamingRound,
    streamingAgents,
    pendingButtIn,
    // Getters
    sortedSessions,
    currentRounds,
    latestRound,
    canExecuteRound,
    sessionProgress,
    // Actions
    fetchSessions,
    loadSession,
    createSession,
    executeRound,
    deleteSession,
    clearCurrentSession,
    toggleAgent,
    clearError,
    // Auto-deliberation actions
    startAutoDeliberation,
    stopAutoDeliberation,
    pauseAutoDeliberation,
    resumeAutoDeliberation,
    stopSession,
    submitButtIn,
  }
})
