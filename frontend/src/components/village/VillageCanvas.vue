<script setup>
/**
 * VillageCanvas - The Village GUI Visualization
 *
 * Canvas-based 2D visualization of agent activity.
 * Agents walk between zones as they execute tools.
 * Now accepts events from parent for shared WebSocket.
 */

import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ZONES, AGENT_COLORS, CANVAS_WIDTH, CANVAS_HEIGHT } from '@/composables/useVillage'

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

const emit = defineEmits(['agentClick', 'zoneClick'])

const canvasRef = ref(null)
let ctx = null
let animationFrameId = null
let agents = new Map()
let activeZone = null

// Agent class
class Agent {
  constructor(id, name, color = '#00aaff') {
    this.id = id
    this.name = name
    this.color = color
    this.radius = 20
    this.x = ZONES.village_square.x
    this.y = ZONES.village_square.y
    this.targetX = this.x
    this.targetY = this.y
    this.state = 'idle'
    this.currentZone = 'village_square'
    this.currentTool = null
    this.moveSpeed = 5
    this.pulsePhase = 0
  }

  moveTo(zoneName) {
    const zone = ZONES[zoneName]
    if (!zone) return
    this.targetX = zone.x
    this.targetY = zone.y
    this.currentZone = zoneName
    this.state = 'moving'
  }

  startTool(toolName) {
    this.currentTool = toolName
    this.state = 'working'
  }

  finishTool() {
    this.currentTool = null
    this.targetX = ZONES.village_square.x
    this.targetY = ZONES.village_square.y
    this.currentZone = 'village_square'
    this.state = 'moving'
  }

  update() {
    const dx = this.targetX - this.x
    const dy = this.targetY - this.y
    const distance = Math.sqrt(dx * dx + dy * dy)

    if (distance > this.moveSpeed) {
      this.x += (dx / distance) * this.moveSpeed
      this.y += (dy / distance) * this.moveSpeed
    } else {
      this.x = this.targetX
      this.y = this.targetY
      if (this.state === 'moving') {
        this.state = this.currentTool ? 'working' : 'idle'
      }
    }
    this.pulsePhase += 0.1
  }

  draw(ctx) {
    ctx.save()
    let radius = this.radius
    if (this.state === 'working') {
      radius += Math.sin(this.pulsePhase) * 3
    }

    // Glow effect
    if (this.state === 'working' || this.state === 'moving') {
      ctx.beginPath()
      ctx.arc(this.x, this.y, radius + 10, 0, Math.PI * 2)
      ctx.fillStyle = this.color + '33'
      ctx.fill()
    }

    // Main circle
    ctx.beginPath()
    ctx.arc(this.x, this.y, radius, 0, Math.PI * 2)
    ctx.fillStyle = this.color
    ctx.fill()
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2
    ctx.stroke()

    // Name label
    ctx.fillStyle = '#ffffff'
    ctx.font = '12px monospace'
    ctx.textAlign = 'center'
    ctx.fillText(this.name, this.x, this.y + radius + 15)

    // Tool label
    if (this.currentTool) {
      ctx.fillStyle = '#ffcc00'
      ctx.font = '10px monospace'
      ctx.fillText(this.currentTool, this.x, this.y - radius - 5)
    }
    ctx.restore()
  }
}

function ensureAgent(agentId) {
  if (!agents.has(agentId)) {
    const color = AGENT_COLORS[agentId] || AGENT_COLORS.default
    agents.set(agentId, new Agent(agentId, agentId, color))
  }
  return agents.get(agentId)
}

// Watch for new events
watch(() => props.events, (newEvents) => {
  if (newEvents.length === 0) return
  const latest = newEvents[0]
  if (!latest) return

  if (latest.type === 'tool_start') {
    const agent = ensureAgent(latest.agent_id)
    agent.moveTo(latest.zone)
    agent.startTool(latest.tool)
    activeZone = latest.zone
  } else if (latest.type === 'tool_complete' || latest.type === 'tool_error') {
    const agent = agents.get(latest.agent_id)
    if (agent) agent.finishTool()
    setTimeout(() => { activeZone = null }, 500)
  }
}, { deep: true })

function drawZone(name, zone, isActive) {
  const halfW = zone.width / 2
  const halfH = zone.height / 2

  ctx.save()
  if (isActive) {
    ctx.shadowColor = zone.color
    ctx.shadowBlur = 20
  }

  ctx.fillStyle = zone.color + '66'
  ctx.strokeStyle = zone.color
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.roundRect(zone.x - halfW, zone.y - halfH, zone.width, zone.height, 10)
  ctx.fill()
  ctx.stroke()

  ctx.fillStyle = '#ffffff'
  ctx.font = '11px monospace'
  ctx.textAlign = 'center'
  ctx.fillText(zone.label, zone.x, zone.y + halfH + 15)
  ctx.restore()
}

function drawConnections() {
  ctx.save()
  ctx.strokeStyle = '#ffffff22'
  ctx.lineWidth = 1
  const center = ZONES.village_square
  for (const [name, zone] of Object.entries(ZONES)) {
    if (name === 'village_square') continue
    ctx.beginPath()
    ctx.moveTo(center.x, center.y)
    ctx.lineTo(zone.x, zone.y)
    ctx.stroke()
  }
  ctx.restore()
}

function render() {
  if (!ctx) return

  // Clear
  ctx.fillStyle = '#1a1a2e'
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)

  // Connections
  drawConnections()

  // Zones
  for (const [name, zone] of Object.entries(ZONES)) {
    drawZone(name, zone, name === activeZone)
  }

  // Agents
  for (const agent of agents.values()) {
    agent.update()
    agent.draw(ctx)
  }

  animationFrameId = requestAnimationFrame(render)
}

function handleClick(event) {
  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  for (const [name, zone] of Object.entries(ZONES)) {
    const halfW = zone.width / 2
    const halfH = zone.height / 2
    if (x >= zone.x - halfW && x <= zone.x + halfW &&
        y >= zone.y - halfH && y <= zone.y + halfH) {
      emit('zoneClick', { name, zone })
      return
    }
  }
}

onMounted(() => {
  if (canvasRef.value) {
    ctx = canvasRef.value.getContext('2d')
    ensureAgent('CLAUDE')
    render()
  }
})

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
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

    <!-- Connection Status -->
    <div class="status-badge">
      <span class="dot" :class="status.connection"></span>
      <span>{{ status.connection }}</span>
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

.status-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.7);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ccc;
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
</style>
