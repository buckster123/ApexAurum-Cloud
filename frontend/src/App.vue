<script setup>
import { watch } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDevMode } from '@/composables/useDevMode'
import Navbar from '@/components/Navbar.vue'
import AlchemicalParticles from '@/components/AlchemicalParticles.vue'

const auth = useAuthStore()
const { pacMode, justActivatedPac } = useDevMode()

// Apply pac-mode class to body for global styling
watch(pacMode, (active) => {
  if (active) {
    document.body.classList.add('pac-mode')
  } else {
    document.body.classList.remove('pac-mode')
  }
}, { immediate: true })
</script>

<template>
  <div
    class="min-h-screen transition-all duration-1000"
    :class="{
      'bg-apex-darker': !pacMode,
      'pac-activate': justActivatedPac
    }"
  >
    <!-- Alchemical floating symbols (PAC mode only) -->
    <AlchemicalParticles />

    <!-- Navbar -->
    <Navbar v-if="auth.isAuthenticated" />

    <!-- Main content -->
    <main :class="auth.isAuthenticated ? 'pt-16' : ''" class="relative z-10">
      <RouterView />
    </main>
  </div>
</template>

<style>
/* Global scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #1a1a1a;
}

::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* PAC mode scrollbar */
.pac-mode ::-webkit-scrollbar-track {
  background: #0a0612;
}

.pac-mode ::-webkit-scrollbar-thumb {
  background: rgba(255, 215, 0, 0.3);
}

.pac-mode ::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 215, 0, 0.5);
}
</style>
