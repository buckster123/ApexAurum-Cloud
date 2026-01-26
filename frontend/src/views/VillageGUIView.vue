<script setup>
/**
 * VillageGUIView - Village GUI Dashboard
 *
 * The main view for watching agents work in the village.
 * "Where invisible computation becomes visible movement"
 */

import { ref, computed } from 'vue'
import { useSound } from '@/composables/useSound'
import VillageCanvas from '@/components/village/VillageCanvas.vue'
import { ZONES, AGENT_COLORS } from '@/composables/useVillage'

const { playTone } = useSound()

const selectedZone = ref(null)
const showLegend = ref(true)

const zones = computed(() => Object.entries(ZONES))
const agents = computed(() => Object.entries(AGENT_COLORS).filter(([k]) => k !== 'default'))

function handleZoneClick({ name, zone }) {
  selectedZone.value = { name, ...zone }
  playTone(440, 0.05, 'sine', 0.1)
}

function closeZoneInfo() {
  selectedZone.value = null
}
</script>

<template>
  <div class="village-gui-view h-screen flex flex-col bg-apex-dark overflow-hidden pt-16">
    <!-- Header -->
    <div class="h-12 bg-apex-dark/80 backdrop-blur border-b border-apex-border flex items-center justify-between px-4">
      <div class="flex items-center gap-3">
        <span class="text-lg">🏘️</span>
        <span class="font-medium text-white">Village GUI</span>
        <span class="text-xs text-gray-500">Agent Activity Visualization</span>
      </div>

      <div class="flex items-center gap-4">
        <!-- Legend Toggle -->
        <button
          @click="showLegend = !showLegend"
          class="text-xs text-gray-400 hover:text-white transition-colors"
        >
          {{ showLegend ? 'Hide' : 'Show' }} Legend
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Canvas Area -->
      <div class="flex-1 flex items-center justify-center p-4">
        <div class="relative">
          <VillageCanvas @zone-click="handleZoneClick" />

          <!-- Zone Info Popup -->
          <div
            v-if="selectedZone"
            class="absolute top-4 left-4 bg-apex-dark/95 border border-apex-border rounded-lg p-4 w-64 z-10"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <span
                  class="w-4 h-4 rounded"
                  :style="{ backgroundColor: selectedZone.color }"
                ></span>
                <span class="font-medium text-white">{{ selectedZone.label }}</span>
              </div>
              <button
                @click="closeZoneInfo"
                class="text-gray-500 hover:text-white"
              >
                &times;
              </button>
            </div>
            <p class="text-xs text-gray-400">
              <template v-if="selectedZone.name === 'dj_booth'">
                Music generation and audio tools. Suno AI integration.
              </template>
              <template v-else-if="selectedZone.name === 'memory_garden'">
                Vector memory, Neo-Cortex, and scratch storage.
              </template>
              <template v-else-if="selectedZone.name === 'file_shed'">
                The Vault - file uploads, downloads, and management.
              </template>
              <template v-else-if="selectedZone.name === 'workshop'">
                Python code execution and evaluation.
              </template>
              <template v-else-if="selectedZone.name === 'bridge_portal'">
                Agent spawning and multi-agent coordination.
              </template>
              <template v-else-if="selectedZone.name === 'library'">
                Knowledge base search and RAG tools.
              </template>
              <template v-else-if="selectedZone.name === 'watchtower'">
                Web fetching, search, and Steel Browser.
              </template>
              <template v-else>
                Default zone for utility tools.
              </template>
            </p>
          </div>
        </div>
      </div>

      <!-- Right Sidebar: Legend -->
      <div
        v-if="showLegend"
        class="w-64 bg-apex-dark border-l border-apex-border p-4 overflow-auto"
      >
        <!-- Zone Legend -->
        <div class="mb-6">
          <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-3">Zones</h3>
          <div class="space-y-2">
            <div
              v-for="[name, zone] in zones"
              :key="name"
              class="flex items-center gap-2 text-sm"
            >
              <span
                class="w-3 h-3 rounded"
                :style="{ backgroundColor: zone.color }"
              ></span>
              <span class="text-gray-300">{{ zone.label }}</span>
            </div>
          </div>
        </div>

        <!-- Agent Legend -->
        <div class="mb-6">
          <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-3">Agents</h3>
          <div class="space-y-2">
            <div
              v-for="[name, color] in agents"
              :key="name"
              class="flex items-center gap-2 text-sm"
            >
              <span
                class="w-3 h-3 rounded-full"
                :style="{ backgroundColor: color }"
              ></span>
              <span class="text-gray-300">{{ name }}</span>
            </div>
          </div>
        </div>

        <!-- Instructions -->
        <div>
          <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-3">How it Works</h3>
          <ul class="text-xs text-gray-400 space-y-2">
            <li>Agents move to zones when executing tools</li>
            <li>Glowing agent = currently working</li>
            <li>Click zones for details</li>
            <li>Activity log shows recent events</li>
          </ul>
        </div>

        <!-- Stats -->
        <div class="mt-6 pt-4 border-t border-apex-border">
          <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-3">Stats</h3>
          <div class="text-xs text-gray-400 space-y-1">
            <div>Total Zones: {{ zones.length }}</div>
            <div>Agent Types: {{ agents.length }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.village-gui-view {
  background: radial-gradient(ellipse at center, #1a1a2e 0%, #0f0f1a 100%);
}
</style>
