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
  CLAUDE: '#4fc3f7',
}

// Available agents for selection
export const AVAILABLE_AGENTS = [
  { id: 'AZOTH', name: 'Azoth', description: 'The Alchemist - Transformation & synthesis' },
  { id: 'VAJRA', name: 'Vajra', description: 'The Thunderbolt - Direct truth & clarity' },
  { id: 'ELYSIAN', name: 'Elysian', description: 'The Muse - Creativity & inspiration' },
  { id: 'KETHER', name: 'Kether', description: 'The Crown - Wisdom & higher perspective' },
  { id: 'CLAUDE', name: 'Claude', description: 'The Assistant - Balanced reasoning' },
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
  }
})
