import { ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useNurseryStore = defineStore('nursery', () => {
  // State
  const datasets = ref([])
  const stats = ref({
    datasets: 0,
    total_examples: 0,
    training_jobs: 0,
    jobs_completed: 0,
    models: 0,
    apprentices: 0,
  })
  const loading = ref(false)
  const generating = ref(false)
  const extracting = ref(false)
  const tierRequired = ref(false)

  // Training Forge state
  const trainingJobs = ref([])
  const trainableModels = ref([])
  const costEstimate = ref(null)
  const estimating = ref(false)
  const startingTraining = ref(false)
  const loadingJobs = ref(false)
  const hasTogetherKey = ref(false)

  // Model Cradle state
  const models = ref([])
  const loadingModels = ref(false)

  // Village Feed state
  const villageActivity = ref([])
  const loadingActivity = ref(false)
  const discoveredModels = ref([])
  const loadingDiscovery = ref(false)
  const discoveryQuery = ref('')

  // Actions
  async function fetchDatasets() {
    loading.value = true
    try {
      const response = await api.get('/api/v1/nursery/datasets')
      datasets.value = response.data.datasets || []
      tierRequired.value = false
    } catch (error) {
      if (error.response?.status === 403) {
        tierRequired.value = true
      }
      console.error('Failed to fetch datasets:', error)
    } finally {
      loading.value = false
    }
  }

  async function generateData(toolNames, numExamples, variationLevel, datasetName) {
    generating.value = true
    try {
      const payload = {
        tool_names: toolNames,
        num_examples: numExamples,
        variation_level: variationLevel,
      }
      if (datasetName) payload.dataset_name = datasetName

      const response = await api.post('/api/v1/nursery/datasets/generate', payload)

      // Refresh list
      await fetchDatasets()
      await fetchStats()

      return response.data
    } catch (error) {
      console.error('Generate failed:', error)
      throw error
    } finally {
      generating.value = false
    }
  }

  async function extractData(toolsFilter, minExamples, datasetName) {
    extracting.value = true
    try {
      const payload = {
        min_examples: minExamples,
      }
      if (toolsFilter && toolsFilter.length > 0) payload.tools_filter = toolsFilter
      if (datasetName) payload.dataset_name = datasetName

      const response = await api.post('/api/v1/nursery/datasets/extract', payload)

      await fetchDatasets()
      await fetchStats()

      return response.data
    } catch (error) {
      console.error('Extract failed:', error)
      throw error
    } finally {
      extracting.value = false
    }
  }

  async function deleteDataset(datasetId) {
    try {
      await api.delete(`/api/v1/nursery/datasets/${datasetId}`)
      datasets.value = datasets.value.filter(d => d.id !== datasetId)
      await fetchStats()
      return true
    } catch (error) {
      console.error('Delete failed:', error)
      return false
    }
  }

  async function fetchStats() {
    try {
      const response = await api.get('/api/v1/nursery/stats')
      stats.value = response.data
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  async function fetchTrainingJobs(statusFilter) {
    loadingJobs.value = true
    try {
      const params = statusFilter ? { status: statusFilter } : {}
      const response = await api.get('/api/v1/nursery/training/jobs', { params })
      trainingJobs.value = response.data.jobs || []
    } catch (error) {
      if (error.response?.status === 403) {
        tierRequired.value = true
      }
      console.error('Failed to fetch training jobs:', error)
    } finally {
      loadingJobs.value = false
    }
  }

  async function fetchTrainableModels() {
    try {
      const response = await api.get('/api/v1/nursery/training/models')
      trainableModels.value = response.data.models || []
    } catch (error) {
      console.error('Failed to fetch trainable models:', error)
    }
  }

  async function estimateCost(datasetId, baseModel, nEpochs, lora) {
    estimating.value = true
    costEstimate.value = null
    try {
      const response = await api.post('/api/v1/nursery/training/estimate', {
        dataset_id: datasetId,
        base_model: baseModel,
        n_epochs: nEpochs,
        lora: lora,
      })
      costEstimate.value = response.data
      return response.data
    } catch (error) {
      console.error('Estimate failed:', error)
      throw error
    } finally {
      estimating.value = false
    }
  }

  async function startTraining(datasetId, baseModel, nEpochs, learningRate, lora, batchSize, suffix) {
    startingTraining.value = true
    try {
      const payload = {
        dataset_id: datasetId,
        base_model: baseModel,
        n_epochs: nEpochs,
        learning_rate: learningRate,
        lora: lora,
      }
      if (batchSize) payload.batch_size = batchSize
      if (suffix) payload.suffix = suffix

      const response = await api.post('/api/v1/nursery/training/start', payload)

      // Refresh jobs and stats
      await fetchTrainingJobs()
      await fetchStats()

      return response.data
    } catch (error) {
      console.error('Start training failed:', error)
      throw error
    } finally {
      startingTraining.value = false
    }
  }

  async function cancelJob(jobId) {
    try {
      await api.post(`/api/v1/nursery/training/jobs/${jobId}/cancel`)
      await fetchTrainingJobs()
      await fetchStats()
      return true
    } catch (error) {
      console.error('Cancel failed:', error)
      return false
    }
  }

  async function checkTogetherKey() {
    try {
      const response = await api.get('/api/v1/api-key/status')
      const providers = response.data.providers || response.data || {}
      const together = providers.together || providers['together'] || {}
      hasTogetherKey.value = !!together.configured
    } catch (error) {
      console.error('Failed to check API key status:', error)
      hasTogetherKey.value = false
    }
  }

  // ── Model Cradle ──────────────────────────────────────────────

  async function fetchModels() {
    loadingModels.value = true
    try {
      const response = await api.get('/api/v1/nursery/models')
      models.value = response.data.models || []
      tierRequired.value = false
    } catch (error) {
      if (error.response?.status === 403) tierRequired.value = true
      console.error('Failed to fetch models:', error)
    } finally {
      loadingModels.value = false
    }
  }

  async function fetchModelDetail(modelId) {
    try {
      const response = await api.get(`/api/v1/nursery/models/${modelId}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch model detail:', error)
      return null
    }
  }

  async function registerModel(modelId) {
    try {
      const response = await api.post(`/api/v1/nursery/models/${modelId}/register`)
      const idx = models.value.findIndex(m => m.id === modelId)
      if (idx !== -1) models.value[idx].village_posted = true
      await fetchStats()
      return response.data
    } catch (error) {
      console.error('Register model failed:', error)
      throw error
    }
  }

  async function deleteModel(modelId) {
    try {
      await api.delete(`/api/v1/nursery/models/${modelId}`)
      models.value = models.value.filter(m => m.id !== modelId)
      await fetchStats()
      return true
    } catch (error) {
      console.error('Delete model failed:', error)
      return false
    }
  }

  // ── Village Feed ──────────────────────────────────────────────

  async function discoverModels(query) {
    loadingDiscovery.value = true
    try {
      const params = {}
      if (query) params.query = query
      const response = await api.get('/api/v1/nursery/discover', { params })
      discoveredModels.value = response.data.models || []
    } catch (error) {
      console.error('Discover models failed:', error)
    } finally {
      loadingDiscovery.value = false
    }
  }

  async function fetchVillageActivity() {
    loadingActivity.value = true
    try {
      const response = await api.get('/api/v1/nursery/village-activity')
      villageActivity.value = response.data.activity || []
    } catch (error) {
      console.error('Failed to fetch village activity:', error)
    } finally {
      loadingActivity.value = false
    }
  }

  return {
    // Data Garden
    datasets, stats, loading, generating, extracting, tierRequired,
    fetchDatasets, generateData, extractData, deleteDataset, fetchStats,
    // Training Forge
    trainingJobs, trainableModels, costEstimate, estimating, startingTraining,
    loadingJobs, hasTogetherKey,
    fetchTrainingJobs, fetchTrainableModels, estimateCost, startTraining, cancelJob, checkTogetherKey,
    // Model Cradle
    models, loadingModels,
    fetchModels, fetchModelDetail, registerModel, deleteModel,
    // Village Feed
    villageActivity, loadingActivity, discoveredModels, loadingDiscovery, discoveryQuery,
    discoverModels, fetchVillageActivity,
  }
})
