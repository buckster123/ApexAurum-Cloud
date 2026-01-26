<script setup>
/**
 * VillageCanvas - The Village GUI Visualization
 *
 * Canvas-based 2D visualization of agent activity.
 * Agents walk between zones as they execute tools.
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useVillage, CANVAS_WIDTH, CANVAS_HEIGHT } from '@/composables/useVillage'

const emit = defineEmits(['agentClick', 'zoneClick'])

const canvasRef = ref(null)
const {
  status,
  eventLog,
  initialize,
  cleanup,
  ZONES
} = useVillage()

// Handle canvas clicks
function handleClick(event) {
  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // Check zone clicks
  for (const [name, zone] of Object.entries(ZONES)) {
    const halfW = zone.width / 2
    const halfH = zone.height / 2

    if (
      x >= zone.x - halfW &&
      x <= zone.x + halfW &&
      y >= zone.y - halfH &&
      y <= zone.y + halfH
    ) {
      emit('zoneClick', { name, zone })
      return
    }
  }
}

onMounted(() => {
  if (canvasRef.value) {
    initialize(canvasRef.value)
  }
})

onUnmounted(() => {
  cleanup()
})
</script>

<template>
  <div class="village-canvas-container">
    <canvas
      ref="canvasRef"
      :width="CANVAS_WIDTH"
      :height="CANVAS_HEIGHT"
      @click="handleClick"
      class="village-canvas"
    />

    <!-- Event Log Overlay -->
    <div class="event-log">
      <div class="event-log-header">
        <span class="dot" :class="status.connection"></span>
        Activity Log
      </div>
      <div class="event-log-content">
        <div
          v-for="(event, idx) in eventLog.slice(0, 10)"
          :key="idx"
          class="event-item"
          :class="event.type"
        >
          <span class="event-agent">{{ event.agent_id }}</span>
          <span class="event-tool">{{ event.tool }}</span>
          <span class="event-status" v-if="event.type === 'tool_complete'">
            {{ event.success ? '✓' : '✗' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.village-canvas-container {
  position: relative;
  display: inline-block;
}

.village-canvas {
  display: block;
  border-radius: 10px;
  cursor: pointer;
}

.event-log {
  position: absolute;
  bottom: 10px;
  right: 10px;
  width: 200px;
  max-height: 150px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid #333;
  border-radius: 8px;
  font-size: 11px;
  overflow: hidden;
}

.event-log-header {
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.1);
  border-bottom: 1px solid #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4444;
}

.dot.connected {
  background: #00ff88;
}

.event-log-content {
  padding: 5px;
  max-height: 110px;
  overflow-y: auto;
}

.event-item {
  padding: 4px 6px;
  border-radius: 4px;
  margin-bottom: 2px;
  display: flex;
  gap: 6px;
  align-items: center;
}

.event-item.tool_start {
  background: rgba(79, 195, 247, 0.2);
}

.event-item.tool_complete {
  background: rgba(0, 255, 136, 0.2);
}

.event-item.tool_error {
  background: rgba(255, 68, 68, 0.2);
}

.event-agent {
  color: #ffd700;
  font-weight: bold;
}

.event-tool {
  color: #ccc;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-status {
  font-size: 12px;
}
</style>
