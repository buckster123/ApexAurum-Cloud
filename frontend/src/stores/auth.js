import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('accessToken'))
  const refreshToken = ref(localStorage.getItem('refreshToken'))
  const initialized = ref(false) // Track if auth check completed

  // Getters - only authenticated if we have a token AND init completed
  const isAuthenticated = computed(() => initialized.value && !!accessToken.value)

  // Actions
  async function login(email, password) {
    const response = await api.post('/api/v1/auth/login', { email, password })
    setTokens(response.data)
    await fetchProfile()
  }

  async function register(email, password, displayName) {
    const response = await api.post('/api/v1/auth/register', {
      email,
      password,
      display_name: displayName
    })
    setTokens(response.data)
    await fetchProfile()
  }

  async function logout() {
    try {
      await api.post('/api/v1/auth/logout')
    } catch (e) {
      // Ignore errors on logout
    }
    clearTokens()
  }

  async function fetchProfile() {
    if (!accessToken.value) return false
    try {
      const response = await api.get('/api/v1/user/profile')
      user.value = response.data
      return true
    } catch (e) {
      console.error('Failed to fetch profile:', e)
      // If 401, token is invalid - clear it
      if (e.response?.status === 401) {
        clearTokens()
      }
      user.value = null
      return false
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      clearTokens()
      return false
    }

    try {
      const response = await api.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken.value
      })
      setTokens(response.data)
      return true
    } catch (e) {
      clearTokens()
      return false
    }
  }

  function setTokens(data) {
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    localStorage.setItem('accessToken', data.access_token)
    localStorage.setItem('refreshToken', data.refresh_token)
  }

  function clearTokens() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  }

  // Initialize: validate token if we have one
  async function initialize() {
    if (accessToken.value) {
      await fetchProfile()
    }
    initialized.value = true
  }

  // Start initialization immediately
  initialize()

  return {
    user,
    accessToken,
    isAuthenticated,
    initialized,
    login,
    register,
    logout,
    fetchProfile,
    refreshAccessToken,
    initialize,
  }
})
