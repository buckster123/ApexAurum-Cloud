/**
 * useVillageIsometric - Isometric 2.5D Village Scene
 *
 * Three.js isometric view of the Village with zone buildings and agent spheres.
 * Fixed camera angle like classic RPGs.
 *
 * "Where agents walk between buildings in isometric splendor"
 */

import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

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
// COMPOSABLE
// ═══════════════════════════════════════════════════════════════════════════

export function useVillageIsometric(containerRef) {
  const isInitialized = ref(false)
  const activeZone = ref(null)

  let scene, camera, renderer
  let animationFrameId
  let zones = {}
  let agents = new Map()
  let clock

  function init() {
    if (!containerRef.value) return false

    const width = containerRef.value.clientWidth
    const height = containerRef.value.clientHeight

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
      agent.finishTool()
    }
    setTimeout(() => setActiveZone(null), 500)
  }

  function animate() {
    if (!isInitialized.value) return

    const deltaTime = clock.getDelta()

    // Update all agents
    for (const agent of agents.values()) {
      agent.update(deltaTime)
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

    for (const agent of agents.values()) {
      agent.dispose()
    }
    agents.clear()

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
    agents,
    ensureAgent,
    handleToolStart,
    handleToolComplete,
    setActiveZone,
    dispose,
    ZONES_3D,
    AGENT_COLORS
  }
}
