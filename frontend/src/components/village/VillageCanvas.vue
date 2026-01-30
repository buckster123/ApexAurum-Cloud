<script setup>
/**
 * VillageCanvas - RPG Pixel Art Village Visualization
 *
 * Canvas-based 2D visualization with pixel art sprites.
 * Agents walk between themed buildings on a grass terrain.
 * "The Athanor's village awakens in pixels"
 */

import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ZONES, AGENT_COLORS, CANVAS_WIDTH, CANVAS_HEIGHT } from '@/composables/useVillage'
import { usePixelSprites } from '@/composables/usePixelSprites'

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

const { initSpriteCache, getSprite, getBuildingSprite, getTerrainTile, SPRITE_SCALE } = usePixelSprites()

// Precomputed terrain canvas (tiled once, reused every frame)
let terrainCanvas = null

function buildTerrainCache() {
  terrainCanvas = document.createElement('canvas')
  terrainCanvas.width = CANVAS_WIDTH
  terrainCanvas.height = CANVAS_HEIGHT
  const tctx = terrainCanvas.getContext('2d')
  tctx.imageSmoothingEnabled = false

  const tile0 = getTerrainTile('grass_0')
  const tile1 = getTerrainTile('grass_1')
  if (!tile0) return

  const tileSize = 16 * SPRITE_SCALE
  for (let y = 0; y < CANVAS_HEIGHT; y += tileSize) {
    for (let x = 0; x < CANVAS_WIDTH; x += tileSize) {
      // Alternate tiles for variety
      const tile = ((Math.floor(x / tileSize) + Math.floor(y / tileSize)) % 3 === 0) ? tile1 : tile0
      tctx.drawImage(tile || tile0, x, y)
    }
  }

  // Draw dirt paths from village square to each zone
  const center = ZONES.village_square
  tctx.strokeStyle = '#8b7355'
  tctx.lineWidth = 18
  tctx.lineCap = 'round'
  for (const [name, zone] of Object.entries(ZONES)) {
    if (name === 'village_square') continue
    tctx.beginPath()
    tctx.moveTo(center.x, center.y)
    tctx.lineTo(zone.x, zone.y)
    tctx.stroke()
  }
  // Path border (darker edges)
  tctx.strokeStyle = '#6b5540'
  tctx.lineWidth = 22
  tctx.globalCompositeOperation = 'destination-over'
  for (const [name, zone] of Object.entries(ZONES)) {
    if (name === 'village_square') continue
    tctx.beginPath()
    tctx.moveTo(center.x, center.y)
    tctx.lineTo(zone.x, zone.y)
    tctx.stroke()
  }
  tctx.globalCompositeOperation = 'source-over'
}

// Sprite-based Agent class
class Agent {
  constructor(id, name, color = '#00aaff') {
    this.id = id
    this.name = name
    this.color = color
    this.x = ZONES.village_square.x
    this.y = ZONES.village_square.y
    this.targetX = this.x
    this.targetY = this.y
    this.state = 'idle'
    this.currentZone = 'village_square'
    this.currentTool = null
    this.moveSpeed = 3 // Slower for RPG feel
    this.pulsePhase = 0

    // Sprite animation state
    this.facing = 'down'
    this.animFrame = 0
    this.animTimer = 0
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

      // Determine facing from movement direction
      if (Math.abs(dx) > Math.abs(dy)) {
        this.facing = dx > 0 ? 'right' : 'left'
      } else {
        this.facing = dy > 0 ? 'down' : 'up'
      }

      // Walk animation (cycle every 200ms at ~60fps)
      this.animTimer += 16
      if (this.animTimer >= 200) {
        this.animTimer = 0
        this.animFrame = (this.animFrame + 1) % 2
      }
    } else {
      this.x = this.targetX
      this.y = this.targetY
      if (this.state === 'moving') {
        this.state = this.currentTool ? 'working' : 'idle'
      }

      // Idle/working animation (slower cycle)
      this.animTimer += 16
      const cycleSpeed = this.state === 'working' ? 250 : 600
      const frameCount = this.state === 'working' ? 3 : 2
      if (this.animTimer >= cycleSpeed) {
        this.animTimer = 0
        this.animFrame = (this.animFrame + 1) % frameCount
      }
    }

    this.pulsePhase += 0.1
  }

  draw(ctx) {
    ctx.save()

    // Determine animation set
    let animation = 'idle'
    if (this.state === 'moving') {
      animation = `walk_${this.facing}`
    } else if (this.state === 'working') {
      animation = 'working'
    }

    const sprite = getSprite(this.name, animation, this.animFrame)

    if (sprite) {
      const drawW = sprite.width
      const drawH = sprite.height
      const drawX = this.x - drawW / 2
      const drawY = this.y - drawH / 2

      // Working glow (behind sprite)
      if (this.state === 'working') {
        const glowRadius = 30 + Math.sin(this.pulsePhase) * 5
        ctx.globalAlpha = 0.2
        ctx.beginPath()
        ctx.arc(this.x, this.y, glowRadius, 0, Math.PI * 2)
        ctx.fillStyle = this.color
        ctx.fill()
        ctx.globalAlpha = 1
      }

      // Moving glow (subtle)
      if (this.state === 'moving') {
        ctx.globalAlpha = 0.1
        ctx.beginPath()
        ctx.arc(this.x, this.y, 25, 0, Math.PI * 2)
        ctx.fillStyle = this.color
        ctx.fill()
        ctx.globalAlpha = 1
      }

      ctx.drawImage(sprite, drawX, drawY)
    } else {
      // Fallback: colored circle (if sprites not loaded)
      ctx.beginPath()
      ctx.arc(this.x, this.y, 20, 0, Math.PI * 2)
      ctx.fillStyle = this.color
      ctx.fill()
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2
      ctx.stroke()
    }

    // Name label
    ctx.fillStyle = '#ffffff'
    ctx.font = '11px monospace'
    ctx.textAlign = 'center'
    ctx.shadowColor = '#000000'
    ctx.shadowBlur = 3
    ctx.fillText(this.name, this.x, this.y + 42)

    // Tool label
    if (this.currentTool) {
      ctx.fillStyle = '#ffcc00'
      ctx.font = '10px monospace'
      ctx.fillText(this.currentTool, this.x, this.y - 42)
    }

    ctx.shadowBlur = 0
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

function drawBuilding(name, zone, isActive) {
  const sprite = getBuildingSprite(name)

  if (sprite) {
    const drawX = zone.x - sprite.width / 2
    const drawY = zone.y - sprite.height / 2

    // Active glow behind building
    if (isActive) {
      ctx.save()
      ctx.globalAlpha = 0.4
      ctx.shadowColor = zone.color
      ctx.shadowBlur = 25
      ctx.drawImage(sprite, drawX, drawY)
      ctx.restore()
    }

    ctx.drawImage(sprite, drawX, drawY)
  } else {
    // Fallback: original rectangle
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
    ctx.restore()
  }

  // Label below building
  ctx.fillStyle = '#ffffff'
  ctx.font = '11px monospace'
  ctx.textAlign = 'center'
  ctx.shadowColor = '#000000'
  ctx.shadowBlur = 3
  ctx.fillText(zone.label, zone.x, zone.y + 55)
  ctx.shadowBlur = 0
}

function render() {
  if (!ctx) return

  // Terrain background (precomputed)
  if (terrainCanvas) {
    ctx.drawImage(terrainCanvas, 0, 0)
  } else {
    ctx.fillStyle = '#2d5a1e'
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
  }

  // Buildings
  for (const [name, zone] of Object.entries(ZONES)) {
    drawBuilding(name, zone, name === activeZone)
  }

  // Agents (drawn on top)
  for (const agent of agents.values()) {
    agent.update()
    agent.draw(ctx)
  }

  animationFrameId = requestAnimationFrame(render)
}

function handleClick(event) {
  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = CANVAS_WIDTH / rect.width
  const scaleY = CANVAS_HEIGHT / rect.height
  const x = (event.clientX - rect.left) * scaleX
  const y = (event.clientY - rect.top) * scaleY

  // Check agent clicks (sprite bounding box)
  const spriteW = 16 * SPRITE_SCALE
  const spriteH = 24 * SPRITE_SCALE
  for (const agent of agents.values()) {
    const halfW = spriteW / 2
    const halfH = spriteH / 2
    if (x >= agent.x - halfW && x <= agent.x + halfW &&
        y >= agent.y - halfH && y <= agent.y + halfH) {
      emit('agentClick', agent.id)
      return
    }
  }

  // Then check zone clicks
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
    // Crisp pixel art (no antialiasing)
    ctx.imageSmoothingEnabled = false

    // Build sprite caches
    initSpriteCache()
    buildTerrainCache()

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
  image-rendering: pixelated;
  image-rendering: crisp-edges;
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
