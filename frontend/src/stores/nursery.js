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

  return {
    datasets,
    stats,
    loading,
    generating,
    extracting,
    tierRequired,
    fetchDatasets,
    generateData,
    extractData,
    deleteDataset,
    fetchStats,
  }
})
