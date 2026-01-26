<script setup>
/**
 * VillageIsometric - Isometric 2.5D Village View
 *
 * Three.js isometric visualization of the village with zone buildings
 * and animated agent spheres.
 */

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useVillageIsometric, ZONES_3D, AGENT_COLORS } from '@/composables/useVillageIsometric'

const props = defineProps({
  events: {
    type: Array,
    default: () => []
  },
  status: {
    type: Object,
    default: () => ({ connection: 'disconnected', eventCount: 0 })
  }
})

const emit = defineEmits(['zone-click', 'agent-click'])

const containerRef = ref(null)

const {
  isInitialized,
  activeZone,
  agents,
  ensureAgent,
  handleToolStart,
  handleToolComplete
} = useVillageIsometric(containerRef)

// Watch for new events
watch(() => props.events, (newEvents) => {
  if (newEvents.length === 0) return

  const latest = newEvents[0]
  if (!latest) return

  if (latest.type === 'tool_start') {
    handleToolStart(latest)
  } else if (latest.type === 'tool_complete' || latest.type === 'tool_error') {
    handleToolComplete(latest)
  }
}, { deep: true })

// Create default agent on mount
onMounted(() => {
  setTimeout(() => {
    if (isInitialized.value) {
      ensureAgent('CLAUDE')
    }
  }, 100)
})
</script>

<template>
  <div class="village-isometric-wrapper relative w-full h-full">
    <!-- Three.js Container -->
    <div
      ref="containerRef"
      class="village-isometric-canvas w-full h-full"
    ></div>

    <!-- Loading overlay -->
    <div
      v-if="!isInitialized"
      class="absolute inset-0 flex items-center justify-center bg-apex-dark"
    >
      <div class="text-center">
        <div class="text-4xl mb-4 animate-pulse">🏘️</div>
        <p class="text-gray-400">Loading Isometric Village...</p>
      </div>
    </div>

    <!-- Connection status -->
    <div class="absolute top-3 left-3 flex items-center gap-2 bg-black/50 backdrop-blur rounded px-3 py-1.5">
      <span
        class="w-2 h-2 rounded-full"
        :class="status.connection === 'connected' ? 'bg-green-400' : 'bg-red-400'"
      ></span>
      <span class="text-xs text-gray-300">{{ status.connection }}</span>
      <span class="text-xs text-gray-500">|</span>
      <span class="text-xs text-gray-400">{{ status.eventCount }} events</span>
    </div>

    <!-- Active zone indicator -->
    <div
      v-if="activeZone"
      class="absolute top-3 right-3 bg-black/50 backdrop-blur rounded px-3 py-1.5"
    >
      <div class="flex items-center gap-2">
        <span
          class="w-3 h-3 rounded"
          :style="{ backgroundColor: ZONES_3D[activeZone]?.color || '#888' }"
        ></span>
        <span class="text-sm text-white">{{ ZONES_3D[activeZone]?.label || activeZone }}</span>
      </div>
    </div>

    <!-- Mini event log -->
    <div class="absolute bottom-3 left-3 w-64 max-h-32 overflow-hidden bg-black/50 backdrop-blur rounded">
      <div class="p-2 border-b border-white/10">
        <span class="text-xs text-gray-400">Recent Activity</span>
      </div>
      <div class="p-2 space-y-1 max-h-24 overflow-auto">
        <div
          v-for="(event, index) in events.slice(0, 5)"
          :key="index"
          class="flex items-center gap-2 text-xs"
        >
          <span
            class="w-2 h-2 rounded-full flex-shrink-0"
            :style="{ backgroundColor: AGENT_COLORS[event.agent_id] || '#888' }"
          ></span>
          <span class="text-gray-400 truncate">{{ event.agent_id }}</span>
          <span class="text-gray-600">→</span>
          <span class="text-white truncate">{{ event.tool }}</span>
          <span
            v-if="event.type === 'tool_complete'"
            :class="event.success ? 'text-green-400' : 'text-red-400'"
          >
            {{ event.success ? '✓' : '✗' }}
          </span>
        </div>
        <div v-if="events.length === 0" class="text-gray-600 text-center py-2">
          No activity yet
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.village-isometric-wrapper {
  background: radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a0f 100%);
}
</style>
