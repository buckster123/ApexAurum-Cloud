<script setup>
/**
 * NeuralSpace - 3D Memory Visualization
 *
 * A Three.js-powered 3D visualization of memories as glowing nodes.
 * "Memories float like stars in the neural cosmos"
 */

import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import * as THREE from 'three'
import { useThreeScene, createMemoryNode, createConnectionLine } from '@/composables/useThreeScene'
import { useNeoCortexStore, AGENT_COLORS, LAYER_CONFIG } from '@/stores/neocortex'
import { useSound } from '@/composables/useSound'

const props = defineProps({
  autoRotate: {
    type: Boolean,
    default: true,
  },
  showConnections: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['select', 'hover', 'doubleClick'])

const store = useNeoCortexStore()
const containerRef = ref(null)

// Initialize Three.js
const {
  scene,
  camera,
  isInitialized,
  getObjectAtMouse,
  focusOn,
  setAutoRotate,
} = useThreeScene(containerRef, {
  backgroundColor: 0x0a0a0f,
  cameraPosition: [0, 50, 100],
  autoRotate: props.autoRotate,
})

// Sound
const { playTone } = useSound()

// Node tracking
const nodeGroup = ref(null)
const connectionGroup = ref(null)
const nodeMap = new Map() // id -> mesh
const hoveredNode = ref(null)
const selectedNode = ref(null)

// Build visualization from graph data
function buildVisualization() {
  if (!scene.value) return

  // Clear existing
  if (nodeGroup.value) {
    scene.value.remove(nodeGroup.value)
  }
  if (connectionGroup.value) {
    scene.value.remove(connectionGroup.value)
  }

  nodeGroup.value = new THREE.Group()
  connectionGroup.value = new THREE.Group()
  nodeMap.clear()

  const nodes = store.filteredNodes
  const edges = store.filteredEdges

  // Create nodes
  nodes.forEach(memory => {
    const mesh = createMemoryNode(memory, AGENT_COLORS, LAYER_CONFIG)
    nodeGroup.value.add(mesh)
    nodeMap.set(memory.id, mesh)
  })

  // Create connections
  if (props.showConnections) {
    edges.forEach(edge => {
      const startMesh = nodeMap.get(edge.source)
      const endMesh = nodeMap.get(edge.target)

      if (startMesh && endMesh) {
        const line = createConnectionLine(
          startMesh.position.toArray(),
          endMesh.position.toArray(),
          edge.type
        )
        connectionGroup.value.add(line)
      }
    })
  }

  scene.value.add(nodeGroup.value)
  scene.value.add(connectionGroup.value)
}

// Mouse handlers
function onMouseMove(event) {
  if (!nodeGroup.value) return

  const intersect = getObjectAtMouse(event, nodeGroup.value.children)

  if (intersect?.object?.userData?.type === 'memory-node') {
    const memory = intersect.object.userData.memory

    // Update hover state
    if (hoveredNode.value !== intersect.object) {
      // Reset previous hover
      if (hoveredNode.value) {
        hoveredNode.value.scale.set(1, 1, 1)
      }

      hoveredNode.value = intersect.object
      intersect.object.scale.set(1.2, 1.2, 1.2)

      store.hoveredMemory = memory
      emit('hover', memory)
    }

    containerRef.value.style.cursor = 'pointer'
  } else {
    // No hover
    if (hoveredNode.value) {
      hoveredNode.value.scale.set(1, 1, 1)
      hoveredNode.value = null
      store.hoveredMemory = null
      emit('hover', null)
    }
    containerRef.value.style.cursor = 'default'
  }
}

function onClick(event) {
  if (!nodeGroup.value) return

  const intersect = getObjectAtMouse(event, nodeGroup.value.children)

  if (intersect?.object?.userData?.type === 'memory-node') {
    const memory = intersect.object.userData.memory

    // Reset previous selection
    if (selectedNode.value) {
      selectedNode.value.material.emissiveIntensity *= 0.5
    }

    // Select new node
    selectedNode.value = intersect.object
    intersect.object.material.emissiveIntensity *= 2

    store.selectMemory(memory)
    emit('select', memory)

    // Sound feedback
    playTone(659, 0.1, 'sine', 0.15)
  }
}

function onDoubleClick(event) {
  if (!nodeGroup.value) return

  const intersect = getObjectAtMouse(event, nodeGroup.value.children)

  if (intersect?.object?.userData?.type === 'memory-node') {
    const memory = intersect.object.userData.memory
    const pos = intersect.object.position.toArray()

    // Focus camera on node
    focusOn(pos)

    emit('doubleClick', memory)

    // Sound feedback
    playTone(880, 0.15, 'sine', 0.2)
  }
}

// Watch for data changes
watch(() => [store.filteredNodes, store.filteredEdges], () => {
  if (isInitialized.value) {
    buildVisualization()
  }
}, { deep: true })

// Watch auto rotate
watch(() => props.autoRotate, (val) => {
  setAutoRotate(val)
})

// Lifecycle
onMounted(() => {
  if (containerRef.value) {
    containerRef.value.addEventListener('mousemove', onMouseMove)
    containerRef.value.addEventListener('click', onClick)
    containerRef.value.addEventListener('dblclick', onDoubleClick)
  }

  // Build visualization when scene is ready
  if (isInitialized.value) {
    buildVisualization()
  } else {
    // Wait for initialization
    const checkInterval = setInterval(() => {
      if (isInitialized.value) {
        buildVisualization()
        clearInterval(checkInterval)
      }
    }, 100)
  }
})

onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('mousemove', onMouseMove)
    containerRef.value.removeEventListener('click', onClick)
    containerRef.value.removeEventListener('dblclick', onDoubleClick)
  }
})

// Expose methods
defineExpose({
  focusOn,
  buildVisualization,
})
</script>

<template>
  <div ref="containerRef" class="neural-space w-full h-full relative">
    <!-- Loading overlay -->
    <div
      v-if="store.isLoading"
      class="absolute inset-0 bg-black/50 flex items-center justify-center z-10"
    >
      <div class="text-center">
        <div class="w-12 h-12 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-gray-400">Loading neural space...</p>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-if="!store.isLoading && store.filteredNodes.length === 0"
      class="absolute inset-0 flex items-center justify-center z-10 pointer-events-none"
    >
      <div class="text-center">
        <div class="text-6xl mb-4 opacity-30">🧠</div>
        <p class="text-gray-500">No memories to display</p>
        <p class="text-gray-600 text-sm mt-2">Memories will appear here as they're created</p>
      </div>
    </div>

    <!-- Hover tooltip -->
    <div
      v-if="store.hoveredMemory"
      class="absolute bottom-4 left-4 bg-apex-dark/90 border border-apex-border rounded-lg p-3 max-w-sm z-10 pointer-events-none"
    >
      <div class="flex items-center gap-2 mb-2">
        <span
          class="w-3 h-3 rounded-full"
          :style="{ backgroundColor: AGENT_COLORS[store.hoveredMemory.agent_id]?.hex || '#888' }"
        ></span>
        <span class="text-xs text-gray-400">{{ store.hoveredMemory.agent_id || 'CLAUDE' }}</span>
        <span class="text-xs text-gray-600">|</span>
        <span class="text-xs text-gray-400">{{ store.hoveredMemory.layer }}</span>
      </div>
      <p class="text-sm text-gray-300 line-clamp-2">
        {{ store.hoveredMemory.content }}
      </p>
    </div>

    <!-- Controls hint -->
    <div class="absolute bottom-4 right-4 text-xs text-gray-600 pointer-events-none">
      Drag to orbit | Scroll to zoom | Click to select | Double-click to focus
    </div>
  </div>
</template>

<style scoped>
.neural-space {
  background: radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a0f 100%);
}
</style>
