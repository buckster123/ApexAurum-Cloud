/**
 * useVillageIsometric - Isometric 2.5D Village Scene
 *
 * Three.js isometric view of the Village with zone buildings and agent spheres.
 * Fixed camera angle like classic RPGs.
 *
 * Phase 5 Polish:
 * - Particle effects on tool completion (green=success, red=error)
 * - Click detection for agents and zones
 * - Speech bubbles for approval/input needed
 *
 * "Where agents walk between buildings in isometric splendor"
 */

import { ref, shallowRef, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

// Polyfill for roundRect (not available in all browsers)
if (typeof CanvasRenderingContext2D !== 'undefined' && !CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, r) {
    if (w < 2 * r) r = w / 2
    if (h < 2 * r) r = h / 2
    this.moveTo(x + r, y)
    this.arcTo(x + w, y, x + w, y + h, r)
    this.arcTo(x + w, y + h, x, y + h, r)
    this.arcTo(x, y + h, x, y, r)
    this.arcTo(x, y, x + w, y, r)
    this.closePath()
    return this
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

export const AGENT_COLORS = {
  AZOTH: '#FFD700',
  CLAUDE: '#00aaff',
  VAJRA: '#4FC3F7',
  ELYSIAN: '#ff69b4',
  KETHER: '#9370db',
  default: '#888888'
}

// Zone configurations with 3D positions
export const ZONES_3D = {
  village_square: {
    position: { x: 0, y: 0, z: 0 },
    size: { w: 8, h: 2, d: 8 },
    color: '#2d3436',
    label: 'Village Square'
  },
  dj_booth: {
    position: { x: -15, y: 0, z: 0 },
    size: { w: 5, h: 4, d: 4 },
    color: '#6c5ce7',
    label: 'DJ Booth'
  },
  memory_garden: {
    position: { x: 0, y: 0, z: -12 },
    size: { w: 7, h: 3, d: 4 },
    color: '#00b894',
    label: 'Memory Garden'
  },
  file_shed: {
    position: { x: 15, y: 0, z: 0 },
    size: { w: 5, h: 4, d: 4 },
    color: '#fdcb6e',
    label: 'File Shed'
  },
  workshop: {
    position: { x: 0, y: 0, z: 12 },
    size: { w: 6, h: 4, d: 4 },
    color: '#e17055',
    label: 'Workshop'
  },
  bridge_portal: {
    position: { x: 12, y: 0, z: -10 },
    size: { w: 5, h: 5, d: 4 },
    color: '#a29bfe',
    label: 'Bridge Portal'
  },
  library: {
    position: { x: -12, y: 0, z: -10 },
    size: { w: 5, h: 4, d: 4 },
    color: '#74b9ff',
    label: 'Library'
  },
  watchtower: {
    position: { x: -12, y: 0, z: 10 },
    size: { w: 4, h: 6, d: 4 },
    color: '#fd79a8',
    label: 'Watchtower'
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// AGENT CLASS (3D)
// ═══════════════════════════════════════════════════════════════════════════

class Agent3D {
  constructor(id, scene, color = '#00aaff') {
    this.id = id
    this.color = color
    this.scene = scene
    this.state = 'idle'
    this.currentZone = 'village_square'
    this.currentTool = null
    this.message = null

    // Target position for movement
    this.targetPosition = new THREE.Vector3(0, 1.5, 0)

    // Create mesh
    this.createMesh()
  }

  createMesh() {
    // Agent sphere
    const geometry = new THREE.SphereGeometry(1, 16, 16)
    const material = new THREE.MeshStandardMaterial({
      color: new THREE.Color(this.color),
      emissive: new THREE.Color(this.color),
      emissiveIntensity: 0.3,
      metalness: 0.2,
      roughness: 0.5
    })

    this.mesh = new THREE.Mesh(geometry, material)
    this.mesh.position.set(0, 1.5, 0)
    this.mesh.userData = { type: 'agent', id: this.id }
    this.scene.add(this.mesh)

    // Glow ring (for working state)
    const ringGeometry = new THREE.RingGeometry(1.2, 1.5, 32)
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: new THREE.Color(this.color),
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide
    })
    this.glowRing = new THREE.Mesh(ringGeometry, ringMaterial)
    this.glowRing.rotation.x = -Math.PI / 2
    this.glowRing.position.y = 0.1
    this.mesh.add(this.glowRing)

    // Name label sprite
    this.createLabel()
  }

  createLabel() {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = 128
    canvas.height = 32

    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 20px monospace'
    ctx.textAlign = 'center'
    ctx.fillText(this.id, 64, 22)

    const texture = new THREE.CanvasTexture(canvas)
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true })
    this.label = new THREE.Sprite(material)
    this.label.scale.set(4, 1, 1)
    this.label.position.y = 2.5
    this.mesh.add(this.label)
  }

  moveTo(zoneName) {
    const zone = ZONES_3D[zoneName]
    if (!zone) return

    this.currentZone = zoneName
    this.targetPosition.set(
      zone.position.x,
      1.5,
      zone.position.z
    )
    this.state = 'moving'
  }

  startTool(toolName) {
    this.currentTool = toolName
    this.state = 'working'
    this.glowRing.material.opacity = 0.6
  }

  finishTool() {
    this.currentTool = null
    this.state = 'moving'
    this.glowRing.material.opacity = 0

    // Return to village square
    this.targetPosition.set(0, 1.5, 0)
    this.currentZone = 'village_square'
  }

  setMessage(msg) {
    this.message = msg
  }

  update(deltaTime) {
    // Smooth movement towards target
    const speed = 0.08
    this.mesh.position.lerp(this.targetPosition, speed)

    // Check if arrived
    if (this.mesh.position.distanceTo(this.targetPosition) < 0.1) {
      if (this.state === 'moving' && !this.currentTool) {
        this.state = 'idle'
      }
    }

    // Pulse animation when working
    if (this.state === 'working') {
      const pulse = Math.sin(Date.now() * 0.005) * 0.15 + 1
      this.mesh.scale.setScalar(pulse)
      this.glowRing.rotation.z += 0.02
    } else {
      this.mesh.scale.setScalar(1)
    }

    // Hover animation when idle
    if (this.state === 'idle') {
      this.mesh.position.y = 1.5 + Math.sin(Date.now() * 0.002) * 0.1
    }
  }

  dispose() {
    this.scene.remove(this.mesh)
    this.mesh.geometry.dispose()
    this.mesh.material.dispose()
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// PARTICLE SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

class ParticleSystem {
  constructor(scene) {
    this.scene = scene
    this.particleGroups = []
  }

  emit(position, color, count = 20, success = true) {
    const geometry = new THREE.BufferGeometry()
    const positions = new Float32Array(count * 3)
    const velocities = []
    const lifetimes = []

    // Initialize particles
    for (let i = 0; i < count; i++) {
      positions[i * 3] = position.x
      positions[i * 3 + 1] = position.y
      positions[i * 3 + 2] = position.z

      // Random velocity (burst outward)
      const theta = Math.random() * Math.PI * 2
      const phi = Math.random() * Math.PI - Math.PI / 2
      const speed = 0.1 + Math.random() * 0.2
      velocities.push({
        x: Math.cos(theta) * Math.cos(phi) * speed,
        y: Math.abs(Math.sin(phi) * speed) + 0.1, // Bias upward
        z: Math.sin(theta) * Math.cos(phi) * speed
      })
      lifetimes.push(1.0) // Full lifetime
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))

    const material = new THREE.PointsMaterial({
      color: new THREE.Color(color),
      size: success ? 0.4 : 0.3,
      transparent: true,
      opacity: 1,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })

    const particles = new THREE.Points(geometry, material)
    this.scene.add(particles)

    this.particleGroups.push({
      mesh: particles,
      velocities,
      lifetimes,
      age: 0,
      maxAge: 1.5
    })
  }

  emitSuccess(position) {
    this.emit(position, '#00ff88', 25, true)
    // Secondary sparkle
    setTimeout(() => this.emit(position, '#ffffff', 10, true), 100)
  }

  emitError(position) {
    this.emit(position, '#ff4444', 20, false)
    this.emit(position, '#ff8800', 10, false)
  }

  update(deltaTime) {
    for (let i = this.particleGroups.length - 1; i >= 0; i--) {
      const group = this.particleGroups[i]
      group.age += deltaTime

      if (group.age >= group.maxAge) {
        // Remove expired particles
        this.scene.remove(group.mesh)
        group.mesh.geometry.dispose()
        group.mesh.material.dispose()
        this.particleGroups.splice(i, 1)
        continue
      }

      // Update positions
      const positions = group.mesh.geometry.attributes.position.array
      const progress = group.age / group.maxAge

      for (let j = 0; j < group.velocities.length; j++) {
        const vel = group.velocities[j]
        positions[j * 3] += vel.x
        positions[j * 3 + 1] += vel.y - 0.01 * group.age // Gravity
        positions[j * 3 + 2] += vel.z
        group.lifetimes[j] -= deltaTime * 0.8
      }

      group.mesh.geometry.attributes.position.needsUpdate = true
      group.mesh.material.opacity = 1 - progress
    }
  }

  dispose() {
    for (const group of this.particleGroups) {
      this.scene.remove(group.mesh)
      group.mesh.geometry.dispose()
      group.mesh.material.dispose()
    }
    this.particleGroups = []
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// SPEECH BUBBLE
// ═══════════════════════════════════════════════════════════════════════════

class SpeechBubble {
  constructor(scene, position, message, type = 'info') {
    this.scene = scene
    this.message = message
    this.type = type
    this.age = 0
    this.maxAge = type === 'approval' ? 30 : 5 // Approval bubbles stay longer

    this.createMesh(position)
  }

  createMesh(position) {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = 256
    canvas.height = 96

    // Background color based on type
    const bgColors = {
      info: 'rgba(40, 40, 60, 0.9)',
      approval: 'rgba(255, 200, 0, 0.95)',
      error: 'rgba(255, 60, 60, 0.9)',
      input: 'rgba(100, 100, 255, 0.9)'
    }

    const textColors = {
      info: '#ffffff',
      approval: '#000000',
      error: '#ffffff',
      input: '#ffffff'
    }

    // Draw bubble
    ctx.fillStyle = bgColors[this.type] || bgColors.info
    ctx.beginPath()
    ctx.roundRect(10, 10, 236, 66, 10)
    ctx.fill()

    // Draw pointer
    ctx.beginPath()
    ctx.moveTo(128 - 10, 76)
    ctx.lineTo(128, 96)
    ctx.lineTo(128 + 10, 76)
    ctx.fill()

    // Draw text
    ctx.fillStyle = textColors[this.type] || textColors.info
    ctx.font = 'bold 16px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    // Wrap text if needed
    const words = this.message.split(' ')
    let line = ''
    let y = 35
    const lineHeight = 20
    const maxWidth = 210

    for (const word of words) {
      const testLine = line + word + ' '
      if (ctx.measureText(testLine).width > maxWidth && line !== '') {
        ctx.fillText(line.trim(), 128, y)
        line = word + ' '
        y += lineHeight
      } else {
        line = testLine
      }
    }
    ctx.fillText(line.trim(), 128, y)

    // Icon for approval type
    if (this.type === 'approval') {
      ctx.font = '20px sans-serif'
      ctx.fillText('⚠️', 30, 43)
    } else if (this.type === 'input') {
      ctx.font = '20px sans-serif'
      ctx.fillText('✏️', 30, 43)
    }

    const texture = new THREE.CanvasTexture(canvas)
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false
    })

    this.sprite = new THREE.Sprite(material)
    this.sprite.scale.set(6, 2.25, 1)
    this.sprite.position.set(position.x, position.y + 4, position.z)
    this.sprite.userData = { type: 'bubble', bubbleType: this.type }

    this.scene.add(this.sprite)
  }

  update(deltaTime, agentPosition) {
    this.age += deltaTime

    // Follow agent
    if (agentPosition) {
      this.sprite.position.x = agentPosition.x
      this.sprite.position.y = agentPosition.y + 4
      this.sprite.position.z = agentPosition.z
    }

    // Fade out near end (except approval which stays)
    if (this.type !== 'approval' && this.age > this.maxAge - 1) {
      this.sprite.material.opacity = this.maxAge - this.age
    }

    // Gentle bob
    this.sprite.position.y += Math.sin(this.age * 3) * 0.01

    return this.age < this.maxAge
  }

  dismiss() {
    this.age = this.maxAge
  }

  dispose() {
    this.scene.remove(this.sprite)
    this.sprite.material.map.dispose()
    this.sprite.material.dispose()
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPOSABLE
// ═══════════════════════════════════════════════════════════════════════════

export function useVillageIsometric(containerRef, options = {}) {
  const isInitialized = ref(false)
  const activeZone = ref(null)
  const selectedAgent = shallowRef(null)
  const hoveredObject = shallowRef(null)

  let scene, camera, renderer
  let animationFrameId
  let zones = {}
  let agents = new Map()
  let clock
  let particleSystem
  let speechBubbles = []
  let raycaster
  let mouse

  function init() {
    if (!containerRef.value) return false

    const width = containerRef.value.clientWidth
    const height = containerRef.value.clientHeight

    // Guard against zero dimensions (can happen if container is hidden)
    if (width === 0 || height === 0) {
      console.warn('Village3D: Container has zero dimensions, skipping init')
      return false
    }

    // Scene
    scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0a0f)

    // Orthographic camera for true isometric
    const aspect = width / height
    const frustumSize = 40
    camera = new THREE.OrthographicCamera(
      -frustumSize * aspect / 2,
      frustumSize * aspect / 2,
      frustumSize / 2,
      -frustumSize / 2,
      0.1,
      1000
    )

    // Isometric camera angle (45° rotation, ~35° tilt)
    camera.position.set(50, 50, 50)
    camera.lookAt(0, 0, 0)

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    containerRef.value.appendChild(renderer.domElement)

    // Lighting
    setupLighting()

    // Ground plane
    createGround()

    // Zone buildings
    createZones()

    // Clock for animations
    clock = new THREE.Clock()

    // Particle system for effects
    particleSystem = new ParticleSystem(scene)

    // Raycaster for click detection
    raycaster = new THREE.Raycaster()
    mouse = new THREE.Vector2()

    // Add event listeners
    renderer.domElement.addEventListener('click', handleClick)
    renderer.domElement.addEventListener('mousemove', handleMouseMove)
    renderer.domElement.style.cursor = 'default'

    isInitialized.value = true
    return true
  }

  function setupLighting() {
    // Ambient light
    const ambient = new THREE.AmbientLight(0x404050, 0.6)
    scene.add(ambient)

    // Main directional light (sun)
    const sun = new THREE.DirectionalLight(0xffffff, 0.8)
    sun.position.set(30, 50, 30)
    sun.castShadow = true
    sun.shadow.mapSize.width = 2048
    sun.shadow.mapSize.height = 2048
    sun.shadow.camera.near = 0.5
    sun.shadow.camera.far = 150
    sun.shadow.camera.left = -40
    sun.shadow.camera.right = 40
    sun.shadow.camera.top = 40
    sun.shadow.camera.bottom = -40
    scene.add(sun)

    // Fill light
    const fill = new THREE.DirectionalLight(0x8080ff, 0.3)
    fill.position.set(-20, 20, -20)
    scene.add(fill)
  }

  function createGround() {
    // Ground plane with grid
    const groundGeometry = new THREE.PlaneGeometry(60, 60)
    const groundMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a2e,
      roughness: 0.9,
      metalness: 0.1
    })
    const ground = new THREE.Mesh(groundGeometry, groundMaterial)
    ground.rotation.x = -Math.PI / 2
    ground.receiveShadow = true
    scene.add(ground)

    // Subtle grid
    const gridHelper = new THREE.GridHelper(60, 30, 0x2a2a3e, 0x2a2a3e)
    gridHelper.position.y = 0.01
    scene.add(gridHelper)
  }

  function createZones() {
    for (const [name, config] of Object.entries(ZONES_3D)) {
      const zone = createZoneBuilding(name, config)
      zones[name] = zone
    }
  }

  function createZoneBuilding(name, config) {
    const { position, size, color, label } = config

    // Building geometry
    const geometry = new THREE.BoxGeometry(size.w, size.h, size.d)
    const material = new THREE.MeshStandardMaterial({
      color: new THREE.Color(color),
      emissive: new THREE.Color(color),
      emissiveIntensity: 0.15,
      roughness: 0.7,
      metalness: 0.1,
      transparent: true,
      opacity: 0.85
    })

    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(position.x, size.h / 2, position.z)
    mesh.castShadow = true
    mesh.receiveShadow = true
    mesh.userData = { type: 'zone', name, label }
    scene.add(mesh)

    // Roof accent
    const roofGeometry = new THREE.BoxGeometry(size.w + 0.2, 0.3, size.d + 0.2)
    const roofMaterial = new THREE.MeshStandardMaterial({
      color: new THREE.Color(color),
      emissive: new THREE.Color(color),
      emissiveIntensity: 0.3,
      roughness: 0.5
    })
    const roof = new THREE.Mesh(roofGeometry, roofMaterial)
    roof.position.y = size.h / 2 + 0.15
    mesh.add(roof)

    // Label
    const labelSprite = createLabelSprite(label)
    labelSprite.position.y = size.h / 2 + 1.5
    mesh.add(labelSprite)

    return { mesh, material, config }
  }

  function createLabelSprite(text) {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = 256
    canvas.height = 64

    ctx.fillStyle = 'rgba(0,0,0,0.6)'
    ctx.fillRect(0, 0, 256, 64)

    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 24px monospace'
    ctx.textAlign = 'center'
    ctx.fillText(text, 128, 40)

    const texture = new THREE.CanvasTexture(canvas)
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true })
    const sprite = new THREE.Sprite(material)
    sprite.scale.set(6, 1.5, 1)
    return sprite
  }

  function ensureAgent(agentId) {
    if (!agents.has(agentId)) {
      const color = AGENT_COLORS[agentId] || AGENT_COLORS.default
      const agent = new Agent3D(agentId, scene, color)
      agents.set(agentId, agent)
    }
    return agents.get(agentId)
  }

  function setActiveZone(zoneName) {
    // Reset previous active zone
    for (const [name, zone] of Object.entries(zones)) {
      zone.material.emissiveIntensity = name === zoneName ? 0.4 : 0.15
    }
    activeZone.value = zoneName
  }

  function handleToolStart(event) {
    const agent = ensureAgent(event.agent_id)
    agent.moveTo(event.zone)
    agent.startTool(event.tool)
    setActiveZone(event.zone)
  }

  function handleToolComplete(event) {
    const agent = agents.get(event.agent_id)
    if (agent) {
      // Emit particles at agent position
      const pos = agent.mesh.position.clone()
      if (event.success !== false) {
        particleSystem.emitSuccess(pos)
      } else {
        particleSystem.emitError(pos)
      }
      agent.finishTool()
    }
    setTimeout(() => setActiveZone(null), 500)
  }

  function handleToolError(event) {
    const agent = agents.get(event.agent_id)
    if (agent) {
      const pos = agent.mesh.position.clone()
      particleSystem.emitError(pos)
      agent.finishTool()

      // Show error bubble
      showBubble(event.agent_id, event.error || 'Error occurred', 'error')
    }
    setTimeout(() => setActiveZone(null), 500)
  }

  function showBubble(agentId, message, type = 'info') {
    const agent = agents.get(agentId)
    if (!agent) return

    // Remove existing bubble for this agent
    dismissBubble(agentId)

    const bubble = new SpeechBubble(scene, agent.mesh.position, message, type)
    bubble.agentId = agentId
    speechBubbles.push(bubble)

    return bubble
  }

  function showApprovalBubble(agentId, message) {
    return showBubble(agentId, message, 'approval')
  }

  function showInputBubble(agentId, message) {
    return showBubble(agentId, message, 'input')
  }

  function dismissBubble(agentId) {
    const idx = speechBubbles.findIndex(b => b.agentId === agentId)
    if (idx !== -1) {
      speechBubbles[idx].dismiss()
    }
  }

  function getMousePosition(event) {
    const rect = renderer.domElement.getBoundingClientRect()
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  }

  function getIntersections() {
    raycaster.setFromCamera(mouse, camera)
    const objects = []

    // Collect agent meshes
    for (const agent of agents.values()) {
      objects.push(agent.mesh)
    }

    // Collect zone meshes
    for (const zone of Object.values(zones)) {
      objects.push(zone.mesh)
    }

    return raycaster.intersectObjects(objects, false)
  }

  function handleClick(event) {
    getMousePosition(event)
    const intersections = getIntersections()

    if (intersections.length > 0) {
      const hit = intersections[0].object
      const userData = hit.userData

      if (userData.type === 'agent') {
        selectedAgent.value = userData.id
        options.onAgentClick?.(userData.id, agents.get(userData.id))
      } else if (userData.type === 'zone') {
        options.onZoneClick?.(userData.name, userData.label)
      }
    } else {
      selectedAgent.value = null
    }
  }

  function handleMouseMove(event) {
    getMousePosition(event)
    const intersections = getIntersections()

    if (intersections.length > 0) {
      const hit = intersections[0].object
      const userData = hit.userData

      if (userData.type === 'agent' || userData.type === 'zone') {
        hoveredObject.value = userData
        renderer.domElement.style.cursor = 'pointer'
      }
    } else {
      hoveredObject.value = null
      renderer.domElement.style.cursor = 'default'
    }
  }

  function animate() {
    if (!isInitialized.value) return

    const deltaTime = clock.getDelta()

    // Update all agents
    for (const agent of agents.values()) {
      agent.update(deltaTime)
    }

    // Update particle system
    if (particleSystem) {
      particleSystem.update(deltaTime)
    }

    // Update speech bubbles
    for (let i = speechBubbles.length - 1; i >= 0; i--) {
      const bubble = speechBubbles[i]
      const agent = agents.get(bubble.agentId)
      const agentPos = agent ? agent.mesh.position : null

      if (!bubble.update(deltaTime, agentPos)) {
        bubble.dispose()
        speechBubbles.splice(i, 1)
      }
    }

    renderer.render(scene, camera)
    animationFrameId = requestAnimationFrame(animate)
  }

  function onResize() {
    if (!containerRef.value || !camera || !renderer) return

    const width = containerRef.value.clientWidth
    const height = containerRef.value.clientHeight
    const aspect = width / height
    const frustumSize = 40

    camera.left = -frustumSize * aspect / 2
    camera.right = frustumSize * aspect / 2
    camera.top = frustumSize / 2
    camera.bottom = -frustumSize / 2
    camera.updateProjectionMatrix()

    renderer.setSize(width, height)
  }

  function dispose() {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId)
    }

    // Remove event listeners
    if (renderer?.domElement) {
      renderer.domElement.removeEventListener('click', handleClick)
      renderer.domElement.removeEventListener('mousemove', handleMouseMove)
    }

    // Dispose agents
    for (const agent of agents.values()) {
      agent.dispose()
    }
    agents.clear()

    // Dispose particles
    if (particleSystem) {
      particleSystem.dispose()
    }

    // Dispose speech bubbles
    for (const bubble of speechBubbles) {
      bubble.dispose()
    }
    speechBubbles = []

    if (renderer) {
      renderer.dispose()
      if (containerRef.value && renderer.domElement) {
        containerRef.value.removeChild(renderer.domElement)
      }
    }

    isInitialized.value = false
  }

  onMounted(() => {
    if (init()) {
      animate()
      window.addEventListener('resize', onResize)
    }
  })

  onUnmounted(() => {
    window.removeEventListener('resize', onResize)
    dispose()
  })

  return {
    isInitialized,
    activeZone,
    selectedAgent,
    hoveredObject,
    agents,
    ensureAgent,
    handleToolStart,
    handleToolComplete,
    handleToolError,
    setActiveZone,
    showBubble,
    showApprovalBubble,
    showInputBubble,
    dismissBubble,
    dispose,
    ZONES_3D,
    AGENT_COLORS
  }
}
